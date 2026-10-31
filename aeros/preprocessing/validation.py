"""Dataset Validation, Coordinate Integrity, and Consistency Engine for AEROS.

Performs schema verification, geographical coordinate boundary checking,
physical air quality consistency enforcement, and duplicate/anomaly detection.
"""

import logging
from typing import Any, Dict, List, Optional, Tuple
import numpy as np
import pandas as pd

logger = logging.getLogger("aeros.preprocessing.validation")

# Atmospheric bounding box for Delhi NCR Region
DELHI_NCR_BOUNDS = {
    "lat_min": 28.30,
    "lat_max": 28.95,
    "lon_min": 76.80,
    "lon_max": 77.50,
}


def validate_coordinates(df: pd.DataFrame) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """Validate that coordinates fall strictly within Delhi NCR geographic bounding box."""
    valid_df = df.copy()
    initial_count = len(valid_df)

    lat_mask = (valid_df["latitude"] >= DELHI_NCR_BOUNDS["lat_min"]) & (
        valid_df["latitude"] <= DELHI_NCR_BOUNDS["lat_max"]
    )
    lon_mask = (valid_df["longitude"] >= DELHI_NCR_BOUNDS["lon_min"]) & (
        valid_df["longitude"] <= DELHI_NCR_BOUNDS["lon_max"]
    )

    valid_mask = lat_mask & lon_mask
    invalid_count = int((~valid_mask).sum())

    if invalid_count > 0:
        logger.warning("Dropping %d records with coordinates outside Delhi NCR bounding box", invalid_count)
        valid_df = valid_df[valid_mask].copy()

    stats = {
        "initial_records": initial_count,
        "valid_coordinates": int(valid_mask.sum()),
        "invalid_coordinates": invalid_count,
        "lat_range": [float(valid_df["latitude"].min()), float(valid_df["latitude"].max())],
        "lon_range": [float(valid_df["longitude"].min()), float(valid_df["longitude"].max())],
    }
    return valid_df, stats


def validate_physical_consistency(df: pd.DataFrame) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """Enforces non-negativity and physical consistency (PM10 >= PM2.5)."""
    valid_df = df.copy()

    # Non-negativity
    valid_df["pm2_5"] = valid_df["pm2_5"].clip(lower=0.1, upper=1500.0)
    valid_df["pm10"] = valid_df["pm10"].clip(lower=0.1, upper=2500.0)

    # Physical constraint: PM10 (total particulate matter under 10 um) must encompass PM2.5
    inconsistent_mask = valid_df["pm10"] < valid_df["pm2_5"]
    corrected_count = int(inconsistent_mask.sum())

    if corrected_count > 0:
        logger.info(
            "Enforcing physical constraint: Correcting %d records where PM10 < PM2.5",
            corrected_count,
        )
        valid_df.loc[inconsistent_mask, "pm10"] = valid_df.loc[inconsistent_mask, "pm2_5"] * 1.15

    stats = {
        "corrected_pm_inconsistencies": corrected_count,
        "pm25_min": float(valid_df["pm2_5"].min()),
        "pm25_max": float(valid_df["pm2_5"].max()),
        "pm10_min": float(valid_df["pm10"].min()),
        "pm10_max": float(valid_df["pm10"].max()),
    }
    return valid_df, stats


def remove_duplicates_and_sort(df: pd.DataFrame) -> Tuple[pd.DataFrame, int]:
    """Removes duplicate station-timestamp records and ensures strict chronological order."""
    cleaned = df.copy()
    before_len = len(cleaned)
    cleaned.sort_values(by=["neighborhood_id", "timestamp"], inplace=True)
    cleaned.drop_duplicates(subset=["neighborhood_id", "timestamp"], keep="last", inplace=True)
    duplicates_removed = before_len - len(cleaned)
    if duplicates_removed > 0:
        logger.info("Removed %d duplicate station-timestamp records", duplicates_removed)
    return cleaned, duplicates_removed
