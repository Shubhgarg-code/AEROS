"""Data Validation, Hygiene and Reconciliation Module for AEROS.

Performs physical validity checks, range clipping, timestamp alignment,
and joins raw air quality and meteorological observations.
"""

import logging
import os
from typing import Dict, Tuple
import numpy as np
import pandas as pd

logger = logging.getLogger("aeros.ingestion.validation")
logging.basicConfig(level=logging.INFO)


def validate_and_clean_air_quality(df: pd.DataFrame) -> pd.DataFrame:
    """Validate physical atmospheric boundaries for air quality."""
    clean_df = df.copy()

    # Sort and remove duplicates
    clean_df.sort_values(by=["neighborhood_id", "timestamp"], inplace=True)
    clean_df.drop_duplicates(
        subset=["neighborhood_id", "timestamp"], keep="last", inplace=True
    )

    # Physical bounds for PM2.5 and PM10
    # In Delhi during severe Diwali episodes, PM2.5 can reach 700-1000 ug/m3, but cannot be negative
    clean_df["pm2_5"] = clean_df["pm2_5"].clip(lower=0.1, upper=1500.0)
    clean_df["pm10"] = clean_df["pm10"].clip(lower=0.1, upper=2500.0)

    # Physical consistency: PM10 (coarse + fine) must be >= PM2.5 (fine fraction)
    # If PM10 is reported less than PM2.5 due to sensor calibration artifact, set PM10 = max(PM10, PM2.5 * 1.05)
    inconsistent_mask = clean_df["pm10"] < clean_df["pm2_5"]
    if inconsistent_mask.any():
        num_inconsistent = inconsistent_mask.sum()
        logger.info(
            "Correcting %d records where PM10 < PM2.5 using physical consistency constraint",
            num_inconsistent,
        )
        clean_df.loc[inconsistent_mask, "pm10"] = (
            clean_df.loc[inconsistent_mask, "pm2_5"] * 1.15
        )

    # Auxiliary pollutants non-negativity
    for col in [
        "nitrogen_dioxide",
        "sulphur_dioxide",
        "ozone",
        "aerosol_optical_depth",
    ]:
        if col in clean_df.columns:
            clean_df[col] = clean_df[col].clip(lower=0.0)

    return clean_df


def validate_and_clean_weather(df: pd.DataFrame) -> pd.DataFrame:
    """Validate physical bounds for meteorological variables."""
    clean_df = df.copy()

    clean_df.sort_values(by=["neighborhood_id", "timestamp"], inplace=True)
    clean_df.drop_duplicates(
        subset=["neighborhood_id", "timestamp"], keep="last", inplace=True
    )

    # Temperature bounds: -5 C to 50 C for Delhi
    if "temperature_2m" in clean_df.columns:
        clean_df["temperature_2m"] = clean_df["temperature_2m"].clip(
            lower=-5.0, upper=50.0
        )

    # Relative humidity: 0% to 100%
    if "relative_humidity_2m" in clean_df.columns:
        clean_df["relative_humidity_2m"] = clean_df[
            "relative_humidity_2m"
        ].clip(lower=0.0, upper=100.0)

    # Wind speed: >= 0 m/s
    if "wind_speed_10m" in clean_df.columns:
        clean_df["wind_speed_10m"] = clean_df["wind_speed_10m"].clip(
            lower=0.0, upper=50.0
        )

    # Wind direction: 0 to 360 degrees
    if "wind_direction_10m" in clean_df.columns:
        clean_df["wind_direction_10m"] = (
            clean_df["wind_direction_10m"] % 360.0
        ).fillna(0.0)

    # Precipitation: >= 0 mm
    if "precipitation" in clean_df.columns:
        clean_df["precipitation"] = clean_df["precipitation"].clip(
            lower=0.0, upper=300.0
        )

    return clean_df


def merge_air_quality_and_weather(
    aq_df: pd.DataFrame,
    weather_df: pd.DataFrame,
    output_dir: str = "aeros/data/processed",
) -> pd.DataFrame:
    """Merge validated air quality and weather data on timestamp and neighborhood."""
    os.makedirs(output_dir, exist_ok=True)

    aq_clean = validate_and_clean_air_quality(aq_df)
    w_clean = validate_and_clean_weather(weather_df)

    # Keep weather join columns
    weather_cols = [
        "neighborhood_id",
        "timestamp",
        "temperature_2m",
        "relative_humidity_2m",
        "surface_pressure",
        "wind_speed_10m",
        "wind_direction_10m",
        "precipitation",
    ]
    w_subset = w_clean[[c for c in weather_cols if c in w_clean.columns]]

    merged = pd.merge(
        aq_clean,
        w_subset,
        on=["neighborhood_id", "timestamp"],
        how="inner",
        suffixes=("", "_w"),
    )

    # Interpolate any isolated internal NaNs per neighborhood time series
    merged.sort_values(by=["neighborhood_id", "timestamp"], inplace=True)
    numeric_cols = merged.select_dtypes(include=[np.number]).columns
    merged[numeric_cols] = merged.groupby("neighborhood_id")[
        numeric_cols
    ].transform(lambda g: g.interpolate(method="linear").bfill().ffill())

    out_path = os.path.join(output_dir, "merged_raw_dataset.parquet")
    merged.to_parquet(out_path, index=False)
    logger.info("Successfully validated and merged dataset. Total rows: %d. Saved to %s", len(merged), out_path)
    return merged
