"""Unit tests for AEROS Data Preprocessing & Physical Validation."""

import numpy as np
import pandas as pd
import pytest

from aeros.preprocessing.cleaning import detect_and_cap_outliers, impute_missing_data
from aeros.preprocessing.validation import (
    remove_duplicates_and_sort,
    validate_coordinates,
    validate_physical_consistency,
)


@pytest.fixture
def sample_raw_dataframe():
    """Provides a synthetic DataFrame with deliberate anomalies for unit testing."""
    records = [
        # Normal record
        {
            "timestamp": "2024-10-31 10:00:00",
            "neighborhood_id": "anand_vihar",
            "latitude": 28.6469,
            "longitude": 77.3160,
            "pm2_5": 150.0,
            "pm10": 280.0,
            "temperature_2m": 24.5,
            "wind_speed_10m": 2.1,
        },
        # Duplicate record
        {
            "timestamp": "2024-10-31 10:00:00",
            "neighborhood_id": "anand_vihar",
            "latitude": 28.6469,
            "longitude": 77.3160,
            "pm2_5": 155.0,
            "pm10": 290.0,
            "temperature_2m": 24.5,
            "wind_speed_10m": 2.1,
        },
        # Physical inconsistency: PM10 < PM2.5
        {
            "timestamp": "2024-10-31 11:00:00",
            "neighborhood_id": "anand_vihar",
            "latitude": 28.6469,
            "longitude": 77.3160,
            "pm2_5": 300.0,
            "pm10": 120.0,  # Inconsistent
            "temperature_2m": 25.0,
            "wind_speed_10m": 1.8,
        },
        # Coordinate out of bounds (lat = 35.0, in Kashmir)
        {
            "timestamp": "2024-10-31 12:00:00",
            "neighborhood_id": "anand_vihar",
            "latitude": 35.0000,
            "longitude": 77.3160,
            "pm2_5": 120.0,
            "pm10": 220.0,
            "temperature_2m": 22.0,
            "wind_speed_10m": 1.5,
        },
        # Record with missing value
        {
            "timestamp": "2024-10-31 13:00:00",
            "neighborhood_id": "anand_vihar",
            "latitude": 28.6469,
            "longitude": 77.3160,
            "pm2_5": np.nan,
            "pm10": 250.0,
            "temperature_2m": 26.0,
            "wind_speed_10m": 1.2,
        },
    ]
    df = pd.DataFrame(records)
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    return df


def test_remove_duplicates(sample_raw_dataframe):
    """Verify duplicate station-timestamp records are identified and removed."""
    cleaned, dup_count = remove_duplicates_and_sort(sample_raw_dataframe)
    assert dup_count == 1
    assert len(cleaned) == len(sample_raw_dataframe) - 1


def test_coordinate_validation(sample_raw_dataframe):
    """Verify points outside Delhi NCR bounds are discarded."""
    valid_df, stats = validate_coordinates(sample_raw_dataframe)
    assert stats["invalid_coordinates"] == 1
    assert (valid_df["latitude"] <= 28.95).all()
    assert (valid_df["latitude"] >= 28.30).all()


def test_physical_consistency_enforcement(sample_raw_dataframe):
    """Verify that PM10 is strictly greater than or equal to PM2.5 for valid values."""
    valid_df, stats = validate_physical_consistency(sample_raw_dataframe)
    assert stats["corrected_pm_inconsistencies"] >= 1
    non_null_mask = valid_df["pm2_5"].notna() & valid_df["pm10"].notna()
    assert (valid_df.loc[non_null_mask, "pm10"] >= valid_df.loc[non_null_mask, "pm2_5"]).all()


def test_missing_value_imputation(sample_raw_dataframe):
    """Verify interpolation and missing value resolution."""
    imputed = impute_missing_data(sample_raw_dataframe)
    assert not imputed["pm2_5"].isna().any()
