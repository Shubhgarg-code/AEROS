"""Unit tests for AEROS Inference, Multi-Horizon Predictions & Uncertainty Bounds."""

import numpy as np
import pytest

from aeros.evaluation.metrics import compute_regression_metrics, evaluate_conformal_calibration
from aeros.models.xgboost_model import AerosXGBoostForecaster


def test_regression_metrics_calculation():
    """Verify standard regression metric outputs and bounds."""
    y_true = np.array([100.0, 150.0, 200.0, 250.0])
    y_pred = np.array([105.0, 145.0, 190.0, 260.0])

    metrics = compute_regression_metrics(y_true, y_pred)
    assert metrics["mae"] > 0.0
    assert metrics["rmse"] >= metrics["mae"]
    assert metrics["r2"] > 0.85
    assert metrics["mape"] > 0.0


def test_conformal_calibration_metrics():
    """Verify conformal coverage computation and interval width."""
    y_true = np.array([100.0, 150.0, 200.0, 250.0])
    q_low = np.array([90.0, 140.0, 190.0, 240.0])
    q_high = np.array([110.0, 160.0, 210.0, 260.0])

    calib = evaluate_conformal_calibration(y_true, q_low, q_high, nominal_coverage=0.90)
    assert calib["empirical_coverage"] == 1.0
    assert calib["mean_interval_width"] == 20.0


def test_xgboost_predict_bounds():
    """Verify non-negativity clipping in predictions."""
    forecaster = AerosXGBoostForecaster(target_name="pm2_5", horizons=[24])
    # Mock residuals
    forecaster.conformal_residuals[24] = np.array([5.0, 10.0, 15.0])

    # Mock model
    class MockModel:
        def predict(self, X):
            return np.array([-5.0, 10.0, 50.0])

    forecaster.models[24] = MockModel()

    preds, lower, upper = forecaster.predict(np.zeros((3, 5)), horizon=24, return_uncertainty=True)
    # Non-negativity constraint
    assert (preds >= 0.0).all()
    assert (lower >= 0.0).all()
    assert (upper >= preds).all()
