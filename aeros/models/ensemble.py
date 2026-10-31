"""Validation-Weighted Ensemble Forecasting Model for AEROS (Model E).

Combines predictions from XGBoost, LSTM, GRU, and Transformer using optimal
validation-derived weights computed via constrained least-squares / inverse RMSE.
"""

import json
import logging
import os
from typing import Any, Dict, List, Optional, Tuple
import numpy as np

from aeros.evaluation.metrics import compute_regression_metrics

logger = logging.getLogger("aeros.models.ensemble")


class AerosEnsembleForecaster:
    """Ensemble forecaster combining predictions from diverse model families."""

    def __init__(self, model_names: Optional[List[str]] = None):
        self.model_names = model_names or ["xgboost", "lstm", "gru", "transformer"]
        self.weights: Dict[str, float] = {}

    def fit_weights_from_validation(
        self,
        val_preds_dict: Dict[str, np.ndarray],
        y_val: np.ndarray,
        metric: str = "rmse",
    ) -> Dict[str, float]:
        """Calculates optimal convex combination weights (w_i >= 0, sum(w_i) = 1) based strictly on validation error."""
        y_val_clean = np.asarray(y_val).ravel()
        errors = {}

        for name, preds in val_preds_dict.items():
            p_clean = np.asarray(preds).ravel()
            metrics = compute_regression_metrics(y_val_clean, p_clean)
            errors[name] = max(metrics[metric], 1e-4)

        # Inverse error weighting: w_i = (1 / err_i^2) / sum(1 / err_j^2)
        inv_sq_errors = {k: 1.0 / (v**2) for k, v in errors.items()}
        total_inv = sum(inv_sq_errors.values())
        self.weights = {k: round(v / total_inv, 4) for k, v in inv_sq_errors.items()}

        logger.info("Fitted validation ensemble weights: %s", self.weights)
        return self.weights

    def predict(self, model_preds_dict: Dict[str, np.ndarray]) -> np.ndarray:
        """Computes weighted ensemble forecast."""
        if not self.weights:
            # Fallback to equal weighting
            n = len(model_preds_dict)
            self.weights = {k: 1.0 / n for k in model_preds_dict.keys()}

        total_weight = sum(self.weights.get(k, 0.0) for k in model_preds_dict.keys())
        if total_weight <= 0:
            raise ValueError("No matching models with positive weights.")

        first_preds = next(iter(model_preds_dict.values()))
        ensemble_pred = np.zeros_like(first_preds, dtype=np.float32)

        for name, preds in model_preds_dict.items():
            w = self.weights.get(name, 0.0)
            ensemble_pred += (w / total_weight) * preds

        return np.clip(ensemble_pred, 0.0, None)

    def save(self, filepath: str = "aeros/artifacts/models/ensemble_weights.json") -> None:
        """Persists ensemble weights."""
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(self.weights, f, indent=2)
        logger.info("Saved ensemble weights to %s", filepath)

    def load(self, filepath: str = "aeros/artifacts/models/ensemble_weights.json") -> None:
        """Loads ensemble weights."""
        with open(filepath, "r", encoding="utf-8") as f:
            self.weights = json.load(f)
        logger.info("Loaded ensemble weights from %s: %s", filepath, self.weights)
