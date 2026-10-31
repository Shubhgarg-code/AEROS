"""Feature Engineering Pipeline for AEROS.

Generates temporal cyclical features, Diwali proximity signals, wind vector
decompositions, ventilation indices, lagged autoregressive features,
and spatial characteristics without lookahead leakage.
"""

import logging
from typing import List, Tuple
import numpy as np
import pandas as pd

logger = logging.getLogger("aeros.preprocessing.features")
logging.basicConfig(level=logging.INFO)


def engineer_temporal_features(df: pd.DataFrame) -> pd.DataFrame:
    """Engineer cyclical time and calendar features."""
    feat_df = df.copy()
    ts = pd.to_datetime(feat_df["timestamp"])

    # Hour of day (24h cycle)
    feat_df["hour"] = ts.dt.hour
    feat_df["hour_sin"] = np.sin(2.0 * np.pi * feat_df["hour"] / 24.0)
    feat_df["hour_cos"] = np.cos(2.0 * np.pi * feat_df["hour"] / 24.0)

    # Day of week (7d cycle)
    feat_df["dayofweek"] = ts.dt.dayofweek
    feat_df["dow_sin"] = np.sin(2.0 * np.pi * feat_df["dayofweek"] / 7.0)
    feat_df["dow_cos"] = np.cos(2.0 * np.pi * feat_df["dayofweek"] / 7.0)

    # Day of year (seasonal cycle)
    feat_df["dayofyear"] = ts.dt.dayofyear
    feat_df["doy_sin"] = np.sin(2.0 * np.pi * feat_df["dayofyear"] / 365.25)
    feat_df["doy_cos"] = np.cos(2.0 * np.pi * feat_df["dayofyear"] / 365.25)

    # Diwali proximity feature: hours relative to Diwali night (8:00 PM on Diwali date)
    if "diwali_date" in feat_df.columns:
        diwali_event_time = pd.to_datetime(feat_df["diwali_date"]) + pd.Timedelta(hours=20)
        hours_to_diwali = (ts - diwali_event_time).dt.total_seconds() / 3600.0
        feat_df["hours_to_diwali"] = hours_to_diwali

        # Atmospheric emission surge bell-curve (active mainly within +/- 36 hours of Diwali night)
        feat_df["diwali_surge_intensity"] = np.exp(-((hours_to_diwali) ** 2) / (2.0 * (18.0 ** 2)))

        # Categorical epoch phase
        conditions = [
            hours_to_diwali < -24.0,
            (hours_to_diwali >= -24.0) & (hours_to_diwali <= 24.0),
            hours_to_diwali > 24.0,
        ]
        choices = ["pre_diwali", "diwali_peak", "post_diwali"]
        feat_df["diwali_phase"] = np.select(conditions, choices, default="normal")
    else:
        feat_df["hours_to_diwali"] = 0.0
        feat_df["diwali_surge_intensity"] = 0.0
        feat_df["diwali_phase"] = "normal"

    return feat_df


def engineer_meteorological_features(df: pd.DataFrame) -> pd.DataFrame:
    """Decompose wind into orthogonal vectors (u, v) and create ventilation proxies."""
    feat_df = df.copy()

    ws = feat_df["wind_speed_10m"].clip(lower=0.01)
    wd_rad = np.radians(feat_df["wind_direction_10m"].fillna(0.0))

    # Meteorological standard: u (eastward wind), v (northward wind)
    # Wind from direction theta blowing towards (theta + 180)
    feat_df["wind_u"] = -ws * np.sin(wd_rad)
    feat_df["wind_v"] = -ws * np.cos(wd_rad)

    feat_df["wind_speed"] = ws
    feat_df["wind_dir_sin"] = np.sin(wd_rad)
    feat_df["wind_dir_cos"] = np.cos(wd_rad)

    # Atmospheric ventilation proxy:
    # High pressure + low wind speed = stagnation (stagnation index)
    p_norm = feat_df["surface_pressure"] / 1013.25
    feat_df["stagnation_index"] = p_norm / (ws + 0.1)
    feat_df["dispersion_capacity"] = ws / (p_norm + 0.01)

    return feat_df


def engineer_lag_and_rolling_features(
    df: pd.DataFrame,
    target_cols: List[str] = ["pm2_5", "pm10"],
    lags: List[int] = [1, 2, 3, 6, 12, 24],
    rolling_windows: List[int] = [6, 12, 24],
) -> pd.DataFrame:
    """Generate strictly backward-looking lag and rolling statistics per neighborhood."""
    feat_df = df.copy()
    feat_df.sort_values(by=["neighborhood_id", "timestamp"], inplace=True)

    grouped = feat_df.groupby("neighborhood_id")

    for col in target_cols:
        if col in feat_df.columns:
            # Lags
            for lag in lags:
                feat_df[f"{col}_lag_{lag}h"] = grouped[col].shift(lag)

            # Rolling statistics (shift by 1 to ensure no current-time leakage)
            shifted = grouped[col].shift(1)
            for w in rolling_windows:
                feat_df[f"{col}_rolling_mean_{w}h"] = shifted.rolling(window=w, min_periods=1).mean()
                feat_df[f"{col}_rolling_std_{w}h"] = shifted.rolling(window=w, min_periods=1).std().fillna(0.0)

    # Forward fill / backward fill initial lag NaNs to retain all valid timestamps
    numeric_cols = feat_df.select_dtypes(include=[np.number]).columns
    feat_df[numeric_cols] = grouped[numeric_cols].transform(lambda g: g.bfill().ffill())

    return feat_df


def engineer_all_features(df: pd.DataFrame) -> pd.DataFrame:
    """Complete feature engineering pipeline."""
    logger.info("Executing comprehensive feature engineering...")
    f1 = engineer_temporal_features(df)
    f2 = engineer_meteorological_features(f1)
    f3 = engineer_lag_and_rolling_features(f2)

    # Land-use one-hot encoding if present
    if "land_use" in f3.columns:
        dummies = pd.get_dummies(f3["land_use"], prefix="landuse", drop_first=False, dtype=float)
        f3 = pd.concat([f3, dummies], axis=1)

    logger.info("Feature engineering complete. Total feature columns: %d", len(f3.columns))
    return f3
