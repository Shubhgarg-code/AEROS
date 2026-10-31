"""Ensemble Training & Validation Optimization Pipeline (Model E).

Gathers predictions from XGBoost, LSTM, GRU, and Transformer,
fits inverse-variance validation weights without lookahead,
and evaluates the combined ensemble against the individual models on the test set.
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
import torch

from aeros.evaluation.metrics import compute_regression_metrics
from aeros.models.ensemble import AerosEnsembleForecaster
from aeros.models.gru import AerosGRU
from aeros.models.lstm import AerosLSTM
from aeros.models.transformer import AerosTransformer
from aeros.models.xgboost_model import AerosXGBoostForecaster
from aeros.training.train_lstm import create_sequences_from_df

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("aeros.training.ensemble")


def train_and_evaluate_ensemble(
    horizon: int = 24,
    lookback: int = 24,
    data_dir: str = "aeros/data/processed",
    scalers_dir: str = "aeros/artifacts/scalers",
    models_dir: str = "aeros/artifacts/models",
    checkpoints_dir: str = "aeros/artifacts/checkpoints",
) -> Tuple[AerosEnsembleForecaster, Dict[str, Any]]:
    """Optimizes ensemble weights using validation set and tests on test set."""
    logger.info("--- Starting Ensemble Training & Evaluation (Horizon: %dh) ---", horizon)

    # 1. Load Data
    val_df = pd.read_parquet(os.path.join(data_dir, "val_temporal.parquet"))
    test_df = pd.read_parquet(os.path.join(data_dir, "test_temporal.parquet"))

    with open(os.path.join(scalers_dir, "feature_columns.json"), "r", encoding="utf-8") as f:
        feature_cols = json.load(f)
    scaler = joblib.load(os.path.join(scalers_dir, "feature_scaler.joblib"))

    # Tabular features for XGBoost
    # Note: Sequences drop the first `lookback` rows per station. Align tabular rows to exact sequence index.
    X_val_seq, y_val_seq = create_sequences_from_df(val_df, feature_cols, scaler, lookback, horizon)
    X_test_seq, y_test_seq = create_sequences_from_df(test_df, feature_cols, scaler, lookback, horizon)

    # Align tabular X for XGBoost using the last step of each sequence
    X_val_tab = X_val_seq[:, -1, :].numpy()
    X_test_tab = X_test_seq[:, -1, :].numpy()

    device = torch.device("cpu")

    # 2. Collect Validation Predictions
    val_preds_dict = {}
    test_preds_dict = {}

    # XGBoost
    try:
        xgb_pm25 = AerosXGBoostForecaster(target_name="pm2_5")
        xgb_pm25.load(models_dir)
        val_preds_dict["xgboost"] = xgb_pm25.predict(X_val_tab, horizon=horizon, return_uncertainty=False)[0]
        test_preds_dict["xgboost"] = xgb_pm25.predict(X_test_tab, horizon=horizon, return_uncertainty=False)[0]
    except Exception as e:
        logger.warning("Could not load XGBoost for ensemble: %s", e)

    # LSTM
    lstm_chk = os.path.join(checkpoints_dir, "best_lstm.pt")
    if os.path.exists(lstm_chk):
        lstm = AerosLSTM(in_features=len(feature_cols), hidden_dim=64, num_layers=2, out_targets=2)
        chk = torch.load(lstm_chk, map_location=device)
        lstm.load_state_dict(chk["model_state_dict"])
        lstm.eval()
        with torch.no_grad():
            val_preds_dict["lstm"] = lstm(X_val_seq).numpy()[:, 0]
            test_preds_dict["lstm"] = lstm(X_test_seq).numpy()[:, 0]

    # GRU
    gru_chk = os.path.join(checkpoints_dir, "best_gru.pt")
    if os.path.exists(gru_chk):
        gru = AerosGRU(in_features=len(feature_cols), hidden_dim=64, num_layers=2, out_targets=2)
        chk = torch.load(gru_chk, map_location=device)
        gru.load_state_dict(chk["model_state_dict"])
        gru.eval()
        with torch.no_grad():
            val_preds_dict["gru"] = gru(X_val_seq).numpy()[:, 0]
            test_preds_dict["gru"] = gru(X_test_seq).numpy()[:, 0]

    # Transformer
    trans_chk = os.path.join(checkpoints_dir, "best_transformer.pt")
    if os.path.exists(trans_chk):
        trans = AerosTransformer(in_features=len(feature_cols), d_model=64, nhead=4, num_layers=2, out_targets=2)
        chk = torch.load(trans_chk, map_location=device)
        trans.load_state_dict(chk["model_state_dict"])
        trans.eval()
        with torch.no_grad():
            val_preds_dict["transformer"] = trans(X_val_seq).numpy()[:, 0]
            test_preds_dict["transformer"] = trans(X_test_seq).numpy()[:, 0]

    y_val_pm25 = y_val_seq[:, 0].numpy()
    y_test_pm25 = y_test_seq[:, 0].numpy()

    # 3. Fit Ensemble Weights strictly on validation set
    ensemble = AerosEnsembleForecaster(model_names=list(val_preds_dict.keys()))
    weights = ensemble.fit_weights_from_validation(val_preds_dict, y_val_pm25, metric="rmse")
    ensemble.save(os.path.join(models_dir, "ensemble_weights.json"))

    # 4. Predict on Test Set
    ensemble_test_pred = ensemble.predict(test_preds_dict)
    ensemble_metrics = compute_regression_metrics(y_test_pm25, ensemble_test_pred, prefix="test_ensemble_pm25_")

    logger.info("Ensemble Test Metrics -> MAE: %.2f, RMSE: %.2f, R2: %.4f",
                ensemble_metrics["test_ensemble_pm25_mae"],
                ensemble_metrics["test_ensemble_pm25_rmse"],
                ensemble_metrics["test_ensemble_pm25_r2"])

    return ensemble, {"weights": weights, "metrics": ensemble_metrics}


if __name__ == "__main__":
    train_and_evaluate_ensemble()
