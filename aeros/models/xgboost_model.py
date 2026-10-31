"""XGBoost Atmospheric Forecaster for AEROS (Model A).

Trains gradient-boosted decision tree ensembles across multiple forecast horizons
(1h, 3h, 6h, 12h, 24h, 48h, 72h) for both PM2.5 and PM10 targets, with feature
importance analysis and conformal uncertainty calibration.
"""

import json
import logging
import os
from typing import Any, Dict, List, Optional, Tuple
import joblib
import numpy as np
import pandas as pd
import xgboost as xgb

from aeros.evaluation.metrics import compute_regression_metrics

logger = logging.getLogger("aeros.models.xgboost")


class AerosXGBoostForecaster:
    """Multi-horizon XGBoost forecasting engine for particulate matter concentrations."""

    def __init__(
        self,
        target_name: str = "pm2_5",
        horizons: List[int] = [1, 3, 6, 12, 24, 48, 72],
        params: Optional[Dict[str, Any]] = None,
    ):
        self.target_name = target_name
        self.horizons = horizons
        self.models: Dict[int, xgb.XGBRegressor] = {}
        self.feature_names: List[str] = []
        self.conformal_residuals: Dict[int, np.ndarray] = {}

        # Default tuned hyperparameters
        self.params = params or {
            "n_estimators": 250,
            "max_depth": 6,
            "learning_rate": 0.04,
            "subsample": 0.85,
            "colsample_bytree": 0.85,
            "reg_alpha": 0.1,
            "reg_lambda": 1.0,
            "random_state": 42,
            "n_jobs": -1,
            "tree_method": "hist",
        }

    def train_horizon(
        self,
        X_train: np.ndarray,
        y_train: np.ndarray,
        X_val: np.ndarray,
        y_val: np.ndarray,
        horizon: int,
        feature_names: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """Trains a specialized XGBoost regressor for a specific forecast horizon."""
        if feature_names:
            self.feature_names = feature_names

        model = xgb.XGBRegressor(
            **self.params,
            early_stopping_rounds=25,
            eval_metric="rmse",
        )

        model.fit(
            X_train,
            y_train,
            eval_set=[(X_val, y_val)],
            verbose=False,
        )

        self.models[horizon] = model

        # Compute validation predictions and residuals for conformal prediction
        val_preds = model.predict(X_val)
        val_metrics = compute_regression_metrics(
            y_val, val_preds, prefix=f"val_{self.target_name}_{horizon}h_"
        )

        # Store calibration residuals for conformal intervals: r = |y - y_hat|
        residuals = np.abs(y_val - val_preds)
        self.conformal_residuals[horizon] = residuals

        logger.info(
            "Trained XGBoost %s %dh -> Val MAE: %.2f, RMSE: %.2f, R2: %.4f (best iteration: %d)",
            self.target_name,
            horizon,
            val_metrics[f"val_{self.target_name}_{horizon}h_mae"],
            val_metrics[f"val_{self.target_name}_{horizon}h_rmse"],
            val_metrics[f"val_{self.target_name}_{horizon}h_r2"],
            model.best_iteration,
        )

        return val_metrics

    def predict(
        self,
        X: np.ndarray,
        horizon: int = 24,
        return_uncertainty: bool = True,
        confidence_level: float = 0.90,
    ) -> Tuple[np.ndarray, Optional[np.ndarray], Optional[np.ndarray]]:
        """Generates point predictions and calibrated conformal prediction intervals."""
        if horizon not in self.models:
            raise ValueError(f"Model for horizon {horizon}h has not been trained.")

        model = self.models[horizon]
        preds = model.predict(X)
        preds = np.clip(preds, 0.0, None)  # Physical non-negativity

        if not return_uncertainty or horizon not in self.conformal_residuals:
            return preds, None, None

        # Conformal prediction interval: y_hat +/- Quantile_{1 - alpha}(residuals)
        residuals = self.conformal_residuals[horizon]
        q_val = float(np.quantile(residuals, confidence_level))

        lower_bound = np.clip(preds - q_val, 0.0, None)
        upper_bound = preds + q_val

        return preds, lower_bound, upper_bound

    def get_feature_importances(
        self, horizon: int = 24, top_n: int = 20
    ) -> List[Dict[str, Any]]:
        """Returns sorted feature importance by gain."""
        if horizon not in self.models:
            return []

        model = self.models[horizon]
        importances = model.feature_importances_

        names = self.feature_names if self.feature_names else [f"f_{i}" for i in range(len(importances))]
        pairs = sorted(zip(names, importances), key=lambda x: x[1], reverse=True)

        return [
            {"feature": k, "importance": round(float(v), 5)}
            for k, v in pairs[:top_n]
        ]

    def save(self, output_dir: str = "aeros/artifacts/models") -> None:
        """Persists trained XGBoost models and conformal calibration residuals."""
        os.makedirs(output_dir, exist_ok=True)
        for h, model in self.models.items():
            model_path = os.path.join(output_dir, f"xgboost_{self.target_name}_{h}h.json")
            model.save_model(model_path)

        meta = {
            "target_name": self.target_name,
            "horizons": self.horizons,
            "feature_names": self.feature_names,
            "conformal_residuals": {
                h: res.tolist() for h, res in self.conformal_residuals.items()
            },
        }
        meta_path = os.path.join(output_dir, f"xgboost_{self.target_name}_meta.joblib")
        joblib.dump(meta, meta_path)
        logger.info("Saved XGBoost models and metadata to %s", output_dir)

    def load(self, model_dir: str = "aeros/artifacts/models") -> None:
        """Loads trained XGBoost models and metadata."""
        meta_path = os.path.join(model_dir, f"xgboost_{self.target_name}_meta.joblib")
        if not os.path.exists(meta_path):
            raise FileNotFoundError(f"XGBoost metadata not found at {meta_path}")

        meta = joblib.load(meta_path)
        self.target_name = meta["target_name"]
        self.horizons = meta["horizons"]
        self.feature_names = meta["feature_names"]
        self.conformal_residuals = {
            int(h): np.array(res) for h, res in meta["conformal_residuals"].items()
        }

        for h in self.horizons:
            model_path = os.path.join(model_dir, f"xgboost_{self.target_name}_{h}h.json")
            if os.path.exists(model_path):
                model = xgb.XGBRegressor()
                model.load_model(model_path)
                self.models[h] = model
        logger.info("Loaded XGBoost %s models for horizons: %s", self.target_name, list(self.models.keys()))
