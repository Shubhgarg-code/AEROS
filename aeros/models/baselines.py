"""Baseline Time-Series Forecasting Models for AEROS.

Provides naive persistence and diurnal seasonal benchmarks required for
scientific model comparison:
1. PersistenceForecaster: y_hat(t+h) = y(t)
2. DiurnalSeasonalForecaster: y_hat(t+h) = y(t + h - 24)
3. HistoricalMeanForecaster: y_hat(t) = Mean(hour, month)
"""

from typing import Dict, List, Optional
import numpy as np
import pandas as pd


class PersistenceForecaster:
    """Naive atmospheric persistence baseline: assumes current pollutant level persists unchanged."""

    def __init__(self, target_col: str = "pm2_5"):
        self.target_col = target_col

    def predict(self, df: pd.DataFrame, horizon: int = 24) -> np.ndarray:
        """Predicts the current value (t) for any lead horizon (t+h)."""
        return df[self.target_col].values.astype(np.float32)


class DiurnalSeasonalForecaster:
    """Diurnal seasonal baseline: predicts the value from 24 hours prior."""

    def __init__(self, target_col: str = "pm2_5"):
        self.target_col = target_col

    def predict(self, df: pd.DataFrame, horizon: int = 24) -> np.ndarray:
        """Uses the 24h lag if available, otherwise current value."""
        lag_col = f"{self.target_col}_lag_24h"
        if lag_col in df.columns:
            return df[lag_col].values.astype(np.float32)
        return df[self.target_col].values.astype(np.float32)


class HistoricalMeanForecaster:
    """Historical profile baseline: predicts the mean for the given hour of day."""

    def __init__(self, target_col: str = "pm2_5"):
        self.target_col = target_col
        self.hour_means: Dict[int, float] = {}
        self.global_mean: float = 0.0

    def fit(self, train_df: pd.DataFrame) -> None:
        """Computes hour-of-day mean profiles on training set."""
        df = train_df.copy()
        if "hour" not in df.columns:
            df["hour"] = pd.to_datetime(df["timestamp"]).dt.hour
        self.global_mean = float(df[self.target_col].mean())
        self.hour_means = df.groupby("hour")[self.target_col].mean().to_dict()

    def predict(self, df: pd.DataFrame, horizon: int = 24) -> np.ndarray:
        """Predicts expected mean based on target lead hour."""
        timestamps = pd.to_datetime(df["timestamp"]) + pd.Timedelta(hours=horizon)
        hours = timestamps.dt.hour
        preds = hours.map(self.hour_means).fillna(self.global_mean).values
        return preds.astype(np.float32)
