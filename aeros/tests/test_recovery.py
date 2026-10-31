"""Unit and Sensitivity Tests for AEROS Atmospheric Recovery Engine.

Validates:
1. Peak pollution detection and timestamp identification.
2. Exponential relaxation decay rate scaling with wind speed, rain, and mixing height.
3. Empirical clearance threshold detection and conformal confidence intervals.
4. Unreached threshold detection with analytical exponential extrapolation.
5. Ventilation sensitivity analysis across atmospheric regimes.
"""

import numpy as np
import pytest

from aeros.inference.recovery_predictor import AerosRecoveryPredictor
from aeros.simulation.recovery import AtmosphericRecoveryEngine


def test_peak_detection():
    """Verifies peak detection index and magnitude."""
    engine = AtmosphericRecoveryEngine()
    series = [60.0, 95.0, 180.0, 340.0, 520.0, 480.0, 310.0, 190.0]
    timestamps = [f"2025-10-20T{h:02d}:00:00" for h in range(len(series))]

    peak = engine.detect_peak(series, timestamps)
    assert peak["peak_index"] == 4
    assert peak["peak_value"] == 520.0
    assert peak["peak_timestamp"] == "2025-10-20T04:00:00"


def test_decay_rate_meteorological_scaling():
    """Verifies that atmospheric relaxation rate accelerates under higher winds and rainfall."""
    engine = AtmosphericRecoveryEngine()

    lambda_stagnant = engine.compute_decay_rate(wind_speed_ms=0.5, rainfall_mm=0.0)
    lambda_moderate = engine.compute_decay_rate(wind_speed_ms=3.0, rainfall_mm=0.0)
    lambda_flushing = engine.compute_decay_rate(wind_speed_ms=6.0, rainfall_mm=0.0)
    lambda_rain = engine.compute_decay_rate(wind_speed_ms=3.0, rainfall_mm=5.0)

    assert lambda_moderate > lambda_stagnant
    assert lambda_flushing > lambda_moderate
    assert lambda_rain > lambda_moderate


def test_empirical_clearance_reached():
    """Verifies clearance time and conformal interval when threshold is crossed within horizon."""
    engine = AtmosphericRecoveryEngine()
    # Peak at hour 3 (450), drops below 60.0 at hour 7 (50.0)
    series = [80.0, 150.0, 300.0, 450.0, 310.0, 180.0, 90.0, 50.0, 42.0]
    timestamps = [f"2025-10-20T{h:02d}:00:00" for h in range(len(series))]

    res = engine.predict_clearance(
        time_series=series,
        target_threshold=60.0,
        timestamps=timestamps,
    )

    assert res["status"] == "THRESHOLD_REACHED"
    assert res["recovery_achieved_within_horizon"] is True
    assert res["clearance_hours_from_peak"] == 4.0  # hour 7 - hour 3
    assert res["clearance_hours_from_start"] == 7.0
    assert res["projected_clearance_timestamp"] == "2025-10-20T07:00:00"

    # Conformal interval check
    ci = res["confidence_interval_90"]
    assert ci[0] <= 4.0 <= ci[1]


def test_clearance_unreached_within_horizon():
    """Verifies analytical extrapolation when concentrations remain elevated above threshold."""
    engine = AtmosphericRecoveryEngine()
    # Highly polluted series that stays above 60.0
    series = [120.0, 250.0, 480.0, 420.0, 380.0, 320.0, 290.0]

    res = engine.predict_clearance(
        time_series=series,
        target_threshold=60.0,
        wind_speed_ms=2.0,
    )

    assert res["status"] == "THRESHOLD_NOT_REACHED_WITHIN_HORIZON"
    assert res["recovery_achieved_within_horizon"] is False
    # Clearance from peak must exceed remaining horizon (7 - 2 = 5 hours)
    assert res["clearance_hours_from_peak"] > 5.0
    assert res["effective_decay_rate_per_hour"] > 0
    assert res["half_life_hours"] > 0


def test_ventilation_sensitivity_spectrum():
    """Verifies clearance time sensitivity decreases monotonically with increasing wind speed."""
    engine = AtmosphericRecoveryEngine()
    table = engine.evaluate_wind_sensitivity(peak_concentration=500.0, target_threshold=60.0)

    assert len(table) >= 5
    # Stagnant regime must take longer to clear than flushing regime
    stagnant_row = table[0]
    flushing_row = table[-1]
    assert stagnant_row["time_to_clear_hours"] > flushing_row["time_to_clear_hours"]

    # Monotonicity check
    hours = [r["time_to_clear_hours"] for r in table]
    assert all(hours[i] >= hours[i + 1] for i in range(len(hours) - 1))


def test_recovery_predictor_wrapper():
    """Tests the high-level AerosRecoveryPredictor wrapper for dual pollutant evaluation."""
    predictor = AerosRecoveryPredictor()
    pm25 = [90.0, 250.0, 450.0, 350.0, 210.0, 110.0, 55.0]
    pm10 = [150.0, 380.0, 650.0, 510.0, 320.0, 180.0, 90.0]

    res = predictor.predict_recovery(
        pm25_series=pm25,
        pm10_series=pm10,
        target_pm25_threshold=60.0,
        target_pm10_threshold=100.0,
    )

    assert "pm25_recovery" in res
    assert "pm10_recovery" in res
    assert "ventilation_sensitivity" in res
    assert res["pm25_recovery"]["status"] == "THRESHOLD_REACHED"
    assert res["pm10_recovery"]["status"] == "THRESHOLD_REACHED"
