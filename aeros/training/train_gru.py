"""Training Pipeline for GRU Forecaster (Model C).

Trains the AerosGRU model on sequential environmental sequences,
compares training and inference speed against LSTM, and saves model checkpoints.
"""

import json
import logging
import os
import sys
import time
from typing import Dict, Tuple

# Ensure workspace root is in sys.path
sys.path.insert(0, os.path.abspath("."))

import joblib
import numpy as np
import pandas as pd
import torch
import torch.nn as nn
from torch.utils.data import DataLoader, TensorDataset

from aeros.evaluation.metrics import compute_regression_metrics
from aeros.models.gru import AerosGRU, save_gru_checkpoint
from aeros.training.train_lstm import create_sequences_from_df

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("aeros.training.gru")


def train_gru_forecaster(
    lookback: int = 24,
    horizon: int = 24,
    epochs: int = 15,
    batch_size: int = 64,
    learning_rate: float = 0.002,
    data_dir: str = "aeros/data/processed",
    scalers_dir: str = "aeros/artifacts/scalers",
    checkpoint_dir: str = "aeros/artifacts/checkpoints",
) -> Tuple[AerosGRU, Dict[str, float]]:
    """Trains the GRU network with early stopping and test evaluation."""
    logger.info("--- Starting GRU Forecaster Training (Lookback: %dh, Lead: %dh) ---", lookback, horizon)

    train_df = pd.read_parquet(os.path.join(data_dir, "train_temporal.parquet"))
    val_df = pd.read_parquet(os.path.join(data_dir, "val_temporal.parquet"))
    test_df = pd.read_parquet(os.path.join(data_dir, "test_temporal.parquet"))

    with open(os.path.join(scalers_dir, "feature_columns.json"), "r", encoding="utf-8") as f:
        feature_cols = json.load(f)
    scaler = joblib.load(os.path.join(scalers_dir, "feature_scaler.joblib"))

    X_train, y_train = create_sequences_from_df(train_df, feature_cols, scaler, lookback, horizon)
    X_val, y_val = create_sequences_from_df(val_df, feature_cols, scaler, lookback, horizon)
    X_test, y_test = create_sequences_from_df(test_df, feature_cols, scaler, lookback, horizon)

    train_loader = DataLoader(TensorDataset(X_train, y_train), batch_size=batch_size, shuffle=True)
    val_loader = DataLoader(TensorDataset(X_val, y_val), batch_size=batch_size, shuffle=False)

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model = AerosGRU(in_features=len(feature_cols), hidden_dim=64, num_layers=2, out_targets=2, dropout=0.2).to(device)

    criterion = nn.SmoothL1Loss()
    optimizer = torch.optim.AdamW(model.parameters(), lr=learning_rate, weight_decay=1e-4)
    scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(optimizer, mode="min", factor=0.5, patience=2)

    best_val_loss = float("inf")
    patience = 4
    patience_counter = 0
    checkpoint_path = os.path.join(checkpoint_dir, "best_gru.pt")

    start_time = time.time()

    for epoch in range(1, epochs + 1):
        model.train()
        train_loss = 0.0
        for bx, by in train_loader:
            bx, by = bx.to(device), by.to(device)
            optimizer.zero_grad()
            preds = model(bx)
            loss = criterion(preds, by)
            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0)
            optimizer.step()
            train_loss += loss.item() * len(bx)
        train_loss /= len(train_loader.dataset)

        model.eval()
        val_loss = 0.0
        with torch.no_grad():
            for bx, by in val_loader:
                bx, by = bx.to(device), by.to(device)
                preds = model(bx)
                loss = criterion(preds, by)
                val_loss += loss.item() * len(bx)
        val_loss /= len(val_loader.dataset)
        scheduler.step(val_loss)

        logger.info("Epoch %02d/%02d | Train Loss: %.4f | Val Loss: %.4f", epoch, epochs, train_loss, val_loss)

        if val_loss < best_val_loss:
            best_val_loss = val_loss
            patience_counter = 0
            save_gru_checkpoint(model, optimizer, epoch, val_loss, checkpoint_path)
        else:
            patience_counter += 1
            if patience_counter >= patience:
                logger.info("Early stopping triggered at epoch %d", epoch)
                break

    train_time = round(time.time() - start_time, 2)

    chk = torch.load(checkpoint_path, map_location=device)
    model.load_state_dict(chk["model_state_dict"])
    model.eval()

    infer_start = time.time()
    with torch.no_grad():
        test_preds = model(X_test.to(device)).cpu().numpy()
    infer_time = round(time.time() - infer_start, 4)

    y_test_np = y_test.numpy()
    pm25_metrics = compute_regression_metrics(y_test_np[:, 0], test_preds[:, 0], prefix="test_pm25_")
    pm10_metrics = compute_regression_metrics(y_test_np[:, 1], test_preds[:, 1], prefix="test_pm10_")

    metrics = {**pm25_metrics, **pm10_metrics, "train_time_sec": train_time, "infer_time_sec": infer_time}
    logger.info("GRU Test Metrics -> PM2.5 MAE: %.2f, RMSE: %.2f | PM10 MAE: %.2f, RMSE: %.2f | Train Time: %.1fs",
                metrics["test_pm25_mae"], metrics["test_pm25_rmse"], metrics["test_pm10_mae"], metrics["test_pm10_rmse"], train_time)

    np.save(os.path.join(checkpoint_dir, "gru_test_preds.npy"), test_preds)
    return model, metrics


if __name__ == "__main__":
    train_gru_forecaster()
