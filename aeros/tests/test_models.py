"""Unit tests for AEROS Model Architectures (Round 3)."""

import numpy as np
import pandas as pd
import pytest
import torch

from aeros.models.baselines import (
    DiurnalSeasonalForecaster,
    HistoricalMeanForecaster,
    PersistenceForecaster,
)
from aeros.models.ensemble import AerosEnsembleForecaster
from aeros.models.gru import AerosGRU
from aeros.models.lstm import AerosLSTM
from aeros.models.transformer import AerosTransformer
from aeros.models.xgboost_model import AerosXGBoostForecaster


def test_baseline_forecasters():
    """Verify persistence and seasonal baselines generate expected outputs."""
    df = pd.DataFrame({
        "timestamp": pd.date_range("2024-11-01", periods=48, freq="h"),
        "pm2_5": [50.0 + i for i in range(48)],
        "pm2_5_lag_24h": [40.0 + i for i in range(48)],
    })

    pers = PersistenceForecaster(target_col="pm2_5")
    p_preds = pers.predict(df, horizon=24)
    assert len(p_preds) == 48
    assert p_preds[0] == 50.0

    seas = DiurnalSeasonalForecaster(target_col="pm2_5")
    s_preds = seas.predict(df, horizon=24)
    assert s_preds[0] == 40.0


def test_lstm_forward_shape():
    """Verify LSTM input and output tensor dimensions."""
    model = AerosLSTM(in_features=72, hidden_dim=32, num_layers=2, out_targets=2)
    x = torch.randn(8, 24, 72)
    out = model(x)
    assert out.shape == (8, 2)
    assert not torch.isnan(out).any()


def test_gru_forward_shape():
    """Verify GRU input and output tensor dimensions."""
    model = AerosGRU(in_features=72, hidden_dim=32, num_layers=2, out_targets=2)
    x = torch.randn(8, 24, 72)
    out = model(x)
    assert out.shape == (8, 2)
    assert not torch.isnan(out).any()


def test_transformer_forward_shape():
    """Verify Transformer input and output tensor dimensions with positional encoding."""
    model = AerosTransformer(in_features=72, d_model=32, nhead=4, num_layers=2, out_targets=2)
    x = torch.randn(8, 24, 72)
    out = model(x)
    assert out.shape == (8, 2)
    assert not torch.isnan(out).any()


def test_ensemble_weight_fitting():
    """Verify ensemble weights sum to 1.0 and prioritize stronger models."""
    ens = AerosEnsembleForecaster()
    y_true = np.array([100.0, 110.0, 120.0, 130.0])
    val_preds = {
        "m_accurate": np.array([101.0, 109.0, 121.0, 129.0]),  # Low error
        "m_poor": np.array([150.0, 160.0, 170.0, 180.0]),      # High error
    }
    weights = ens.fit_weights_from_validation(val_preds, y_true, metric="rmse")
    assert abs(sum(weights.values()) - 1.0) < 1e-3
    assert weights["m_accurate"] > weights["m_poor"]
