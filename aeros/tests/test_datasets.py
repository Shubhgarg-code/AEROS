"""Unit tests for AEROS Dataset Splitting, Scaler Integrity, and Sequence Generation."""

import numpy as np
import pandas as pd
import pytest
from sklearn.preprocessing import RobustScaler

from aeros.preprocessing.dataset_builder import build_and_save_datasets
from aeros.preprocessing.datasets import (
    create_multi_horizon_targets,
    partition_chronological_splits,
    partition_spatial_holdout,
)


@pytest.fixture
def multi_year_sample_df():
    """Generates multi-year dataset spanning 2021-2025 across 4 stations."""
    records = []
    stations = ["anand_vihar", "ito", "dwarka", "lodhi_road"]
    years = [2021, 2022, 2023, 2024, 2025]

    for year in years:
        times = pd.date_range(f"{year}-11-01", periods=100, freq="h")
        for st in stations:
            for i, t in enumerate(times):
                records.append({
                    "timestamp": t,
                    "neighborhood_id": st,
                    "diwali_year": year,
                    "pm2_5": 100.0 + (year - 2021) * 20.0 + i * 0.5,
                    "pm10": 200.0 + (year - 2021) * 30.0 + i * 0.8,
                    "temperature_2m": 22.0,
                    "wind_speed": 2.5,
                })
    return pd.DataFrame(records)


def test_chronological_split_integrity(multi_year_sample_df):
    """Verify that training, validation, and testing years are completely disjoint."""
    train_df, val_df, test_df = partition_chronological_splits(
        multi_year_sample_df,
        train_years=[2021, 2022, 2023],
        val_years=[2024],
        test_years=[2025],
    )

    assert set(train_df["diwali_year"].unique()) == {2021, 2022, 2023}
    assert set(val_df["diwali_year"].unique()) == {2024}
    assert set(test_df["diwali_year"].unique()) == {2025}

    # Verify chronological ordering
    assert train_df["timestamp"].max() < val_df["timestamp"].min()
    assert val_df["timestamp"].max() < test_df["timestamp"].min()


def test_spatial_holdout_isolation(multi_year_sample_df):
    """Verify that spatial holdout neighborhoods never appear in monitored training data."""
    holdout = ["dwarka"]
    sp_train, sp_holdout = partition_spatial_holdout(multi_year_sample_df, holdout_neighborhoods=holdout)

    assert "dwarka" not in sp_train["neighborhood_id"].unique()
    assert "dwarka" in sp_holdout["neighborhood_id"].unique()
    assert sp_holdout["neighborhood_id"].nunique() == 1


def test_multi_horizon_targets_synthesis(multi_year_sample_df):
    """Verify forward lead target calculation."""
    df_leads = create_multi_horizon_targets(multi_year_sample_df, target_cols=["pm2_5"], horizons=[1, 3, 6])
    assert "pm2_5_lead_1h" in df_leads.columns
    assert "pm2_5_lead_3h" in df_leads.columns
    assert "pm2_5_lead_6h" in df_leads.columns

    # Verify lead 1h matches next hour's target for same station
    st_group = df_leads[df_leads["neighborhood_id"] == "anand_vihar"].sort_values("timestamp")
    assert st_group["pm2_5_lead_1h"].iloc[0] == st_group["pm2_5"].iloc[1]
