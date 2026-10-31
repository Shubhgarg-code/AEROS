"""Training Pipeline for XGBoost Forecaster (Model A).

Trains multi-horizon XGBoost models on historical air quality and weather features,
evaluates on chronological validation and test partitions, and saves model checkpoints.
"""

import json
import logging
import os
import sys
from typing import Any, Dict, List, Optional, Tuple

# Ensure workspace root is in sys.path
sys.path.insert(0, os.path.abspath("."))

import joblib
import numpy as np
import pandas as pd

from aeros.evaluation.metrics import compute_regression_metrics
from aeros.models.xgboost_model import AerosXGBoostForecaster

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("aeros.training.xgboost")


def run_xgboost_training(
    target_name: str = "pm2_5",
    horizons: list = [1, 3, 6, 12, 24, 48, 72],
    data_dir: str = "aeros/data/processed",
    scalers_dir: str = "aeros/artifacts/scalers",
    models_dir: str = "aeros/artifacts/models",
) -> Tuple[AerosXGBoostForecaster, Dict[str, Any]]:
    """Trains and evaluates XGBoost forecaster across specified horizons."""
    logger.info("--- Starting XGBoost Training for %s across horizons %s ---", target_name, horizons)

    # 1. Load Data
    train_df = pd.read_parquet(os.path.join(data_dir, "train_temporal.parquet"))
    val_df = pd.read_parquet(os.path.join(data_dir, "val_temporal.parquet"))
    test_df = pd.read_parquet(os.path.join(data_dir, "test_temporal.parquet"))

    # 2. Load Feature Columns and Scaler
    with open(os.path.join(scalers_dir, "feature_columns.json"), "r", encoding="utf-8") as f:
        feature_cols = json.load(f)

    feature_scaler = joblib.load(os.path.join(scalers_dir, "feature_scaler.joblib"))

    X_train = feature_scaler.transform(train_df[feature_cols])
    X_val = feature_scaler.transform(val_df[feature_cols])
    X_test = feature_scaler.transform(test_df[feature_cols])

    forecaster = AerosXGBoostForecaster(target_name=target_name, horizons=horizons)
    results = {"val": {}, "test": {}}

    for h in horizons:
        lead_col = f"{target_name}_lead_{h}h"
        y_train = train_df[lead_col].values.astype(np.float32)
        y_val = val_df[lead_col].values.astype(np.float32)
        y_test = test_df[lead_col].values.astype(np.float32)

        # Train for this horizon
        val_metrics = forecaster.train_horizon(
            X_train=X_train,
            y_train=y_train,
            X_val=X_val,
            y_val=y_val,
            horizon=h,
            feature_names=feature_cols,
        )
        results["val"][f"{h}h"] = val_metrics

        # Test evaluation
        test_preds, q_low, q_high = forecaster.predict(X_test, horizon=h, return_uncertainty=True)
        test_metrics = compute_regression_metrics(y_test, test_preds, prefix=f"test_{target_name}_{h}h_")
        results["test"][f"{h}h"] = test_metrics

        logger.info(
            "XGBoost Test %s %dh -> MAE: %.2f, RMSE: %.2f, R2: %.4f",
            target_name,
            h,
            test_metrics[f"test_{target_name}_{h}h_mae"],
            test_metrics[f"test_{target_name}_{h}h_rmse"],
            test_metrics[f"test_{target_name}_{h}h_r2"],
        )

    # 3. Save model artifacts
    forecaster.save(output_dir=models_dir)
    return forecaster, results


if __name__ == "__main__":
    # Train both PM2.5 and PM10
    fc_pm25, res_pm25 = run_xgboost_training(target_name="pm2_5")
    fc_pm10, res_pm10 = run_xgboost_training(target_name="pm10")
    logger.info("XGBoost training for PM2.5 and PM10 completed successfully.")
