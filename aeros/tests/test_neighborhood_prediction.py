"""Unit tests for Neighborhood-Level Air Quality Prediction Engine (Round 4)."""

import pytest

from aeros.inference.neighborhood_predictor import AerosNeighborhoodPredictor


@pytest.fixture
def predictor():
    """Provides instantiated neighborhood predictor."""
    return AerosNeighborhoodPredictor()


def test_predict_valid_delhi_coordinate(predictor):
    """Verify inference for a landmark coordinate inside Delhi (India Gate: 28.6129, 77.2295)."""
    res = predictor.predict_coordinate(latitude=28.6129, longitude=77.2295)
    assert res["status"] == "SUCCESS"
    assert "pm2_5" in res
    assert "pm10" in res

    pm25 = res["pm2_5"]
    assert pm25["point_estimate"] > 0.0
    assert pm25["lower_bound"] <= pm25["point_estimate"]
    assert pm25["upper_bound"] >= pm25["point_estimate"]
    assert pm25["unit"] == "µg/m³"

    target = res["target_location"]
    assert target["confidence_rating"] in ["HIGH", "MODERATE", "LOW"]
    assert target["distance_to_nearest_monitor_km"] < 15.0


def test_predict_out_of_bounds_coordinate(predictor):
    """Verify that coordinates outside Delhi NCR are gracefully rejected."""
    res = predictor.predict_coordinate(latitude=12.9716, longitude=77.5946)  # Bengaluru
    assert res["status"] == "OUT_OF_BOUNDS"
    assert res["data_available"] is False


def test_uncertainty_expansion_with_distance(predictor):
    """Verify that prediction interval expands as distance from physical monitor increases."""
    # Near central Delhi (close to monitors)
    near = predictor.predict_coordinate(latitude=28.6289, longitude=77.2407)
    # Further out near border
    far = predictor.predict_coordinate(latitude=28.8500, longitude=76.9500)

    near_width = near["pm2_5"]["upper_bound"] - near["pm2_5"]["lower_bound"]
    far_width = far["pm2_5"]["upper_bound"] - far["pm2_5"]["lower_bound"]

    # Farther point must have strictly larger uncertainty interval
    assert far_width > near_width
