"""Spatial Interpolation and Machine Learning Baselines for AEROS.

Provides:
1. Inverse Distance Weighting (IDW) interpolation
2. Spatial Nearest-Station Baseline
3. Spatial XGBoost regressor (trained on monitored stations, evaluated on holdout stations)
"""

from typing import Any, Dict, List, Optional, Tuple
import numpy as np
import pandas as pd
import xgboost as xgb

from aeros.evaluation.metrics import compute_regression_metrics
from aeros.ingestion.geospatial import haversine_distance_km
from aeros.spatial.distance_features import compute_idw_weights


class InverseDistanceWeightingInterpolator:
    """IDW Spatial Interpolator using monitored station observations."""

    def __init__(self, power: float = 2.0):
        self.power = power

    def predict_point(
        self,
        target_lat: float,
        target_lon: float,
        station_lats: List[float],
        station_lons: List[float],
        station_values: np.ndarray,
    ) -> float:
        """Interpolates scalar pollutant concentration at target coordinates."""
        source_coords = list(zip(station_lats, station_lons))
        weights = compute_idw_weights((target_lat, target_lon), source_coords, power=self.power)
        return float(np.sum(weights * np.asarray(station_values)))

    def evaluate_holdout(
        self,
        monitored_df: pd.DataFrame,
        holdout_df: pd.DataFrame,
        target_col: str = "pm2_5",
    ) -> Dict[str, float]:
        """Evaluates IDW zero-shot interpolation on held-out geographical stations across all shared timestamps."""
        # Align by timestamp
        preds, true_vals = [], []
        timestamps = sorted(list(set(monitored_df["timestamp"]).intersection(set(holdout_df["timestamp"]))))

        for ts in timestamps:
            mon_slice = monitored_df[monitored_df["timestamp"] == ts]
            hold_slice = holdout_df[holdout_df["timestamp"] == ts]

            if len(mon_slice) == 0 or len(hold_slice) == 0:
                continue

            st_lats = mon_slice["latitude"].tolist()
            st_lons = mon_slice["longitude"].tolist()
            st_vals = mon_slice[target_col].values

            for _, row in hold_slice.iterrows():
                pred = self.predict_point(row["latitude"], row["longitude"], st_lats, st_lons, st_vals)
                preds.append(pred)
                true_vals.append(row[target_col])

        return compute_regression_metrics(np.array(true_vals), np.array(preds), prefix=f"idw_{target_col}_")


class SpatialXGBoostBaseline:
    """XGBoost regressor equipped with spatial coordinate and road density features."""

    def __init__(self):
        self.model_pm25 = xgb.XGBRegressor(n_estimators=150, max_depth=5, learning_rate=0.05, random_state=42)
        self.model_pm10 = xgb.XGBRegressor(n_estimators=150, max_depth=5, learning_rate=0.05, random_state=42)

    def fit_and_evaluate(
        self,
        train_monitored_df: pd.DataFrame,
        holdout_df: pd.DataFrame,
        feature_cols: List[str],
        scaler,
    ) -> Dict[str, Any]:
        """Trains on monitored stations and evaluates on unseen holdout stations."""
        X_train = scaler.transform(train_monitored_df[feature_cols])
        X_holdout = scaler.transform(holdout_df[feature_cols])

        # Train PM2.5
        self.model_pm25.fit(X_train, train_monitored_df["pm2_5"].values)
        pm25_preds = self.model_pm25.predict(X_holdout)

        # Train PM10
        self.model_pm10.fit(X_train, train_monitored_df["pm10"].values)
        pm10_preds = self.model_pm10.predict(X_holdout)

        m_pm25 = compute_regression_metrics(holdout_df["pm2_5"].values, pm25_preds, prefix="spatial_xgb_pm25_")
        m_pm10 = compute_regression_metrics(holdout_df["pm10"].values, pm10_preds, prefix="spatial_xgb_pm10_")
        return {**m_pm25, **m_pm10}
