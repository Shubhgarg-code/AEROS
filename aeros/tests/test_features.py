"""Unit tests for AEROS Feature Engineering Pipeline."""

import numpy as np
import pandas as pd
import pytest

from aeros.preprocessing.features import (
    engineer_lag_and_rolling_features,
    engineer_meteorological_features,
    engineer_temporal_features,
)


@pytest.fixture
def feature_sample_df():
    """Generates synthetic multi-day time series for feature verification."""
    times = pd.date_range("2023-11-10 00:00:00", periods=72, freq="h")
    df = pd.DataFrame({
        "timestamp": times,
        "neighborhood_id": "ito",
        "diwali_date": pd.to_datetime("2023-11-12"),
        "pm2_5": [100.0 + i * 2.0 for i in range(72)],
        "pm10": [200.0 + i * 3.5 for i in range(72)],
        "temperature_2m": [22.0 + 5.0 * np.sin(i / 12.0) for i in range(72)],
        "relative_humidity_2m": [60.0 + 10.0 * np.cos(i / 12.0) for i in range(72)],
        "surface_pressure": [1012.0 for _ in range(72)],
        "wind_speed_10m": [2.5 for _ in range(72)],
        "wind_direction_10m": [315.0 for _ in range(72)],  # NW Wind
        "precipitation": [0.0 for _ in range(72)],
    })
    return df


def test_temporal_features(feature_sample_df):
    """Verify cyclic hour and Diwali surge features."""
    feat = engineer_temporal_features(feature_sample_df)
    assert "hour_sin" in feat.columns
    assert "hour_cos" in feat.columns
    assert "hours_to_diwali" in feat.columns
    assert "diwali_surge_intensity" in feat.columns

    # Check bounds of trigonometric features
    assert (feat["hour_sin"] >= -1.0 - 1e-5).all() and (feat["hour_sin"] <= 1.0 + 1e-5).all()
    assert (feat["hour_cos"] >= -1.0 - 1e-5).all() and (feat["hour_cos"] <= 1.0 + 1e-5).all()

    # Peak Diwali surge should be ~1.0 near Diwali night
    assert feat["diwali_surge_intensity"].max() > 0.95


def test_meteorological_wind_decomposition(feature_sample_df):
    """Verify wind u and v orthogonal component extraction."""
    feat = engineer_meteorological_features(feature_sample_df)
    assert "wind_u" in feat.columns
    assert "wind_v" in feat.columns
    assert "stagnation_index" in feat.columns

    # Wind speed magnitude reconstruction: sqrt(u^2 + v^2) == ws
    reconstructed_speed = np.sqrt(feat["wind_u"] ** 2 + feat["wind_v"] ** 2)
    np.testing.assert_allclose(reconstructed_speed, feat["wind_speed"], rtol=1e-3)


def test_lag_features_no_lookahead(feature_sample_df):
    """Verify lagged values correspond strictly to past hours."""
    feat = engineer_lag_and_rolling_features(feature_sample_df, target_cols=["pm2_5"], lags=[1, 2, 3])
    assert "pm2_5_lag_1h" in feat.columns

    # Row 10's 1-hour lag must match Row 9's original value
    assert feat["pm2_5_lag_1h"].iloc[10] == feature_sample_df["pm2_5"].iloc[9]
    assert feat["pm2_5_lag_2h"].iloc[10] == feature_sample_df["pm2_5"].iloc[8]
