"""Unit and Counterfactual Policy Tests for AEROS What-If Simulation Engine.

Validates:
1. Scenario configurations and parameter sanity.
2. Diurnal vehicular traffic curve and episodic pyrotechnic emission pulse profiles.
3. Monotonic physical response: firecracker reductions lower peak pollution; increases raise it.
4. Combined policy mitigation effectiveness.
5. Absence of non-physical negative concentrations.
"""

import numpy as np
import pytest

from aeros.simulation.counterfactual import DiwaliWhatIfSimulator
from aeros.simulation.scenarios import (
    SCENARIO_REGISTRY,
    ScenarioType,
    compute_diurnal_traffic_profile,
    compute_firecracker_emission_pulse,
)


def test_scenario_registry_integrity():
    """Verifies that all 7 required scenarios are registered with valid non-negative multipliers."""
    assert len(SCENARIO_REGISTRY) == 7
    for sc_type, cfg in SCENARIO_REGISTRY.items():
        assert cfg.scenario_type == sc_type
        assert cfg.firecracker_multiplier >= 0.0
        assert cfg.traffic_multiplier >= 0.0
        assert cfg.pblh_multiplier > 0.0
        assert isinstance(cfg.name, str) and len(cfg.name) > 0


def test_diurnal_traffic_profile():
    """Verifies that diurnal traffic emissions exhibit realistic morning/evening rush hour peaks."""
    rush_morning = compute_diurnal_traffic_profile(9.0)
    rush_evening = compute_diurnal_traffic_profile(18.5)
    midday = compute_diurnal_traffic_profile(13.5)
    midnight = compute_diurnal_traffic_profile(2.5)

    assert rush_morning > midday
    assert rush_evening > midday
    assert midday > midnight
    assert midnight >= 0.2


def test_firecracker_emission_pulse_shape():
    """Verifies pyrotechnic pulse timing, decay, and high PM2.5 fine-particulate ratio."""
    # Peak at relative hour 3.5 (~21:30 PM on Diwali night)
    s25_peak, s10_peak = compute_firecracker_emission_pulse(3.5)
    s25_early, _ = compute_firecracker_emission_pulse(0.0)
    s25_late, _ = compute_firecracker_emission_pulse(9.0)
    s25_outside, _ = compute_firecracker_emission_pulse(15.0)

    assert s25_peak > s25_early
    assert s25_peak > s25_late
    assert s25_outside == 0.0

    # PM2.5 / PM10 ratio should be ~0.72 (fine particle dominated)
    assert pytest.approx(s25_peak / s10_peak, rel=1e-3) == 0.72


def test_counterfactual_monotonicity_and_policy_impact():
    """Verifies that policy interventions produce monotonic and scientifically consistent results."""
    sim = DiwaliWhatIfSimulator()
    # 24-hour simulation starting on Diwali night
    duration = 24
    start_t = "2025-10-20T18:00:00"

    baseline = sim.simulate_scenario(
        ScenarioType.BASELINE,
        duration_hours=duration,
        start_time_iso=start_t,
        diwali_night_iso=start_t,
    )
    fc_increase = sim.simulate_scenario(
        ScenarioType.FIRECRACKER_INCREASE,
        duration_hours=duration,
        start_time_iso=start_t,
        diwali_night_iso=start_t,
    )
    fc_reduction = sim.simulate_scenario(
        ScenarioType.FIRECRACKER_REDUCTION,
        duration_hours=duration,
        start_time_iso=start_t,
        diwali_night_iso=start_t,
    )
    combined = sim.simulate_scenario(
        ScenarioType.COMBINED_MITIGATION,
        duration_hours=duration,
        start_time_iso=start_t,
        diwali_night_iso=start_t,
    )
    weather_flush = sim.simulate_scenario(
        ScenarioType.WEATHER_FLUSHING,
        duration_hours=duration,
        start_time_iso=start_t,
        diwali_night_iso=start_t,
    )

    # 1. Monotonicity checks on peak PM2.5
    assert fc_increase["peak_pm25"] > baseline["peak_pm25"]
    assert fc_reduction["peak_pm25"] < baseline["peak_pm25"]
    assert combined["peak_pm25"] <= fc_reduction["peak_pm25"]

    # 2. Cumulative exposure checks
    assert combined["cumulative_exposure_pm25"] < baseline["cumulative_exposure_pm25"]
    assert weather_flush["cumulative_exposure_pm25"] < baseline["cumulative_exposure_pm25"]

    # 3. Non-negativity check
    for series in [
        baseline["hourly_mean_pm25_series"],
        fc_increase["hourly_mean_pm25_series"],
        fc_reduction["hourly_mean_pm25_series"],
        combined["hourly_mean_pm25_series"],
    ]:
        assert all(val >= 0.0 for val in series)

    # 4. Population-weighted exposure index
    assert combined["population_weighted_exposure_index"] < baseline["population_weighted_exposure_index"]


def test_scenario_comparison_batch():
    """Verifies batch scenario comparison table generation."""
    sim = DiwaliWhatIfSimulator()
    start_t = "2025-10-20T18:00:00"
    comp = sim.compare_all_scenarios(
        scenarios=[ScenarioType.BASELINE, ScenarioType.FIRECRACKER_REDUCTION],
        start_time_iso=start_t,
        diwali_night_iso=start_t,
        duration_hours=12,
    )

    assert comp["reference_scenario"] == ScenarioType.BASELINE.value
    assert len(comp["comparison_table"]) == 2
    row_reduction = next(r for r in comp["comparison_table"] if r["scenario_type"] == "firecracker_reduction")
    assert row_reduction["delta_peak_pm25"] < 0
    assert row_reduction["delta_cumulative_exposure_pct"] < 0
