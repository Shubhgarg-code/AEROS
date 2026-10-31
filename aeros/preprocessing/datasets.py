"""Dataset Partitioning, Multi-Horizon Sequence Generation, and Scaler Management for AEROS.

Enforces strict chronological train/val/test splits and spatial holdouts.
Fits scalers strictly on training data to prevent lookahead leakage.
"""

import json
import logging
import os
from typing import Any, Dict, List, Optional, Tuple
import joblib
import numpy as np
import pandas as pd
from sklearn.preprocessing import RobustScaler

logger = logging.getLogger("aeros.preprocessing.datasets")
logging.basicConfig(level=logging.INFO)

DEFAULT_HORIZONS = [1, 3, 6, 12, 24, 48, 72]


def create_multi_horizon_targets(
    df: pd.DataFrame,
    target_cols: List[str] = ["pm2_5", "pm10"],
    horizons: List[int] = DEFAULT_HORIZONS,
) -> pd.DataFrame:
    """Creates multi-step forward lead target columns without lookahead leakage."""
    target_df = df.copy()
    target_df.sort_values(by=["neighborhood_id", "timestamp"], inplace=True)
    grouped = target_df.groupby("neighborhood_id")

    for col in target_cols:
        for h in horizons:
            target_df[f"{col}_lead_{h}h"] = grouped[col].shift(-h)

    # Drop rows at the end of each series where future targets are unknown
    max_h = max(horizons)
    valid_mask = target_df.groupby("neighborhood_id").cumcount(ascending=False) >= max_h
    filtered_df = target_df[valid_mask].copy()
    return filtered_df


def partition_chronological_splits(
    df: pd.DataFrame,
    train_years: List[int] = [2021, 2022, 2023],
    val_years: List[int] = [2024],
    test_years: List[int] = [2025],
) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Chronological split by year to evaluate real future generalization."""
    train_df = df[df["diwali_year"].isin(train_years)].copy()
    val_df = df[df["diwali_year"].isin(val_years)].copy()
    test_df = df[df["diwali_year"].isin(test_years)].copy()

    logger.info(
        "Chronological split sizes -> Train: %d, Val: %d, Test: %d",
        len(train_df),
        len(val_df),
        len(test_df),
    )
    return train_df, val_df, test_df


def partition_spatial_holdout(
    df: pd.DataFrame,
    holdout_neighborhoods: List[str] = ["dwarka", "jahangirpuri", "mandir_marg"],
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """Splits dataset into monitored training locations and unmonitored holdout locations."""
    spatial_train_df = df[~df["neighborhood_id"].isin(holdout_neighborhoods)].copy()
    spatial_holdout_df = df[df["neighborhood_id"].isin(holdout_neighborhoods)].copy()

    logger.info(
        "Spatial partition -> Monitored stations: %d rows (%d locations), Holdout stations: %d rows (%d locations)",
        len(spatial_train_df),
        spatial_train_df["neighborhood_id"].nunique(),
        len(spatial_holdout_df),
        spatial_holdout_df["neighborhood_id"].nunique(),
    )
    return spatial_train_df, spatial_holdout_df


class AerosDataPipeline:
    """End-to-end data pipeline managing preprocessing, scalers, and PyTorch sequences."""

    def __init__(
        self,
        scaler_dir: str = "aeros/artifacts/scalers",
        horizons: List[int] = DEFAULT_HORIZONS,
    ):
        self.scaler_dir = scaler_dir
        self.horizons = horizons
        os.makedirs(scaler_dir, exist_ok=True)
        self.feature_scaler = RobustScaler()
        self.target_scaler_pm25 = RobustScaler()
        self.target_scaler_pm10 = RobustScaler()
        self.feature_cols: List[str] = []

    def get_feature_column_names(self, df: pd.DataFrame) -> List[str]:
        """Identifies all numerical input features, excluding identifiers and forward targets."""
        exclude_cols = [
            "timestamp",
            "neighborhood_id",
            "neighborhood_name",
            "diwali_date",
            "diwali_year",
            "diwali_phase",
            "land_use",
            "zone",
        ]
        exclude_prefixes = ["pm2_5_lead_", "pm10_lead_"]

        features = []
        for col in df.columns:
            if col in exclude_cols:
                continue
            if any(col.startswith(p) for p in exclude_prefixes):
                continue
            if np.issubdtype(df[col].dtype, np.number):
                features.append(col)

        return sorted(features)

    def fit_scalers(self, train_df: pd.DataFrame) -> None:
        """Fit scalers strictly on training data."""
        self.feature_cols = self.get_feature_column_names(train_df)
        logger.info("Fitting RobustScaler on %d feature columns...", len(self.feature_cols))

        self.feature_scaler.fit(train_df[self.feature_cols])
        self.target_scaler_pm25.fit(train_df[["pm2_5"]])
        self.target_scaler_pm10.fit(train_df[["pm10"]])

        joblib.dump(self.feature_scaler, os.path.join(self.scaler_dir, "feature_scaler.joblib"))
        joblib.dump(self.target_scaler_pm25, os.path.join(self.scaler_dir, "pm25_scaler.joblib"))
        joblib.dump(self.target_scaler_pm10, os.path.join(self.scaler_dir, "pm10_scaler.joblib"))

        # Save feature column list for inference alignment
        with open(os.path.join(self.scaler_dir, "feature_columns.json"), "w", encoding="utf-8") as f:
            json.dump(self.feature_cols, f, indent=2)

        logger.info("Saved fitted scalers and feature columns to %s", self.scaler_dir)

    def transform_features(self, df: pd.DataFrame) -> np.ndarray:
        """Transform features using fitted scaler."""
        return self.feature_scaler.transform(df[self.feature_cols])

    def build_tabular_dataset(
        self, df: pd.DataFrame, target: str = "pm2_5", horizon: int = 24
    ) -> Tuple[np.ndarray, np.ndarray]:
        """Extracts tabular X, y for tree-based models like XGBoost."""
        target_col = f"{target}_lead_{horizon}h"
        valid = df.dropna(subset=[target_col] + self.feature_cols)
        X = self.feature_scaler.transform(valid[self.feature_cols])
        y = valid[target_col].values.astype(np.float32)
        return X, y

    def build_sequential_dataset(
        self,
        df: pd.DataFrame,
        lookback: int = 24,
        target_col: str = "pm2_5",
        horizon: int = 24,
    ) -> Tuple[np.ndarray, np.ndarray]:
        """Creates sliding time-series windows [N, lookback, F] -> [N, 1] for LSTM/Transformer."""
        lead_col = f"{target_col}_lead_{horizon}h"
        sequences, targets = [], []

        for _, group in df.groupby("neighborhood_id"):
            group_sorted = group.sort_values(by="timestamp").reset_index(drop=True)
            if len(group_sorted) <= lookback:
                continue

            feat_vals = self.feature_scaler.transform(group_sorted[self.feature_cols])
            y_vals = group_sorted[lead_col].values

            for i in range(lookback, len(group_sorted)):
                if np.isnan(y_vals[i - 1]):
                    continue
                sequences.append(feat_vals[i - lookback : i])
                targets.append(y_vals[i - 1])

        return np.array(sequences, dtype=np.float32), np.array(targets, dtype=np.float32)
