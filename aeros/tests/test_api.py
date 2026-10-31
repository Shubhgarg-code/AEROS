"""Integration Tests for AEROS FastAPI Endpoints."""

import pytest
from aeros.api.routes import (
    compare_scenarios,
    get_models_metadata,
    get_overview,
    get_stations,
    predict_air_quality,
    predict_neighborhood,
    predict_recovery,
    predict_spatial,
    simulate_propagation,
    simulate_scenario,
    simulation_health,
)
from aeros.api.schemas import (
    AirQualityPredictionRequest,
    NeighborhoodPredictionRequest,
    PropagationSimulationRequest,
    RecoveryPredictionRequest,
    ScenarioComparisonRequest,
    ScenarioSimulationRequest,
    SpatialPredictionRequest,
)
from aeros.simulation.scenarios import ScenarioType


def test_simulation_health_endpoint():
    """Verifies health check endpoint returns 121 cells, 15 stations, 7 scenarios."""
    health = simulation_health()
    assert health["status"] == "HEALTHY"
    assert health["spatial_grid"]["total_cells"] == 121
    assert health["monitored_stations_count"] == 15
    assert len(health["supported_scenarios"]) == 7


def test_predict_neighborhood_endpoint():
    """Verifies spatial coordinate estimation via API handler."""
    req = NeighborhoodPredictionRequest(
        latitude=28.6139,
        longitude=77.2090,
        weather_conditions={"wind_speed": 2.5},
    )
    res = predict_neighborhood(req)
    assert res["status"] == "SUCCESS"
    assert res["pm2_5"]["point_estimate"] > 0
    assert res["pm10"]["point_estimate"] >= res["pm2_5"]["point_estimate"]
    assert res["target_location"]["confidence_rating"] in ["HIGH", "MODERATE", "LOW"]


def test_simulate_scenario_endpoint():
    """Verifies single scenario simulation via API handler."""
    req = ScenarioSimulationRequest(
        scenario_type=ScenarioType.BASELINE,
        duration_hours=6,
        start_time_iso="2025-10-20T18:00:00",
        diwali_night_iso="2025-10-20T18:00:00",
    )
    res = simulate_scenario(req)
    assert res["scenario_type"] == "baseline"
    assert res["peak_pm25"] > 0
    assert len(res["hourly_mean_pm25_series"]) == 7  # 0 to 6
    assert res["cumulative_exposure_pm25"] > 0


def test_compare_scenarios_endpoint():
    """Verifies multi-scenario comparison via API handler."""
    req = ScenarioComparisonRequest(
        scenarios=[ScenarioType.BASELINE, ScenarioType.FIRECRACKER_REDUCTION],
        duration_hours=8,
    )
    res = compare_scenarios(req)
    assert res["reference_scenario"] == "baseline"
    assert len(res["comparison_table"]) == 2


def test_predict_recovery_endpoint():
    """Verifies post-peak atmospheric recovery endpoint."""
    req = RecoveryPredictionRequest(
        pm25_series=[90.0, 220.0, 480.0, 310.0, 190.0, 110.0, 52.0],
        target_pm25_threshold=60.0,
        wind_speed_ms=3.0,
    )
    res = predict_recovery(req)
    assert res["pm25_recovery"]["status"] == "THRESHOLD_REACHED"
    assert res["pm25_recovery"]["clearance_hours_from_peak"] == 4.0
    assert len(res["ventilation_sensitivity"]) >= 5


def test_simulate_propagation_endpoint():
    """Verifies 2D propagation rollout and GeoJSON export via API handler."""
    req = PropagationSimulationRequest(
        duration_hours=3,
        initial_pm25={"anand_vihar": 160.0},
        initial_pm10={"anand_vihar": 240.0},
    )
    res = simulate_propagation(req)
    assert "simulation_id" in res
    assert "peak_hour_geojson" in res
    assert res["peak_hour_geojson"]["type"] == "FeatureCollection"
    assert len(res["peak_hour_geojson"]["features"]) == 121


def test_overview_endpoint():
    """Verifies overview endpoint returns citywide AQI, 15 stations, alerts."""
    ov = get_overview()
    assert ov.status == "SUCCESS"
    assert ov.city == "Delhi NCR"
    assert len(ov.stations) == 15
    assert ov.citywide_aqi > 0
    assert len(ov.active_alerts) >= 1


def test_stations_endpoint():
    """Verifies stations endpoint returns list with coordinates and metadata."""
    st = get_stations()
    assert st["status"] == "SUCCESS"
    assert st["count"] == 15
    assert len(st["stations"]) == 15
    assert "latitude" in st["stations"][0]


def test_air_quality_forecast_endpoint():
    """Verifies multi-horizon temporal forecasting endpoint."""
    req = AirQualityPredictionRequest(
        neighborhood_id="anand_vihar",
        horizon_hours=24,
    )
    res = predict_air_quality(req)
    assert res["status"] == "SUCCESS"
    assert res["predicted_pm25"] > 0
    assert len(res["hourly_timeline"]) == 24
    assert len(res["feature_importance"]) >= 3


def test_predict_spatial_endpoint():
    """Verifies spatial intelligence estimation with supporting stations."""
    req = SpatialPredictionRequest(
        latitude=28.6139,
        longitude=77.2090,
    )
    res = predict_spatial(req)
    assert res["status"] == "SUCCESS"
    assert "supporting_stations" in res
    assert len(res["supporting_stations"]) == 4
    assert "model_comparison" in res


def test_models_metadata_endpoint():
    """Verifies transparency metadata endpoint returns benchmark comparison tables."""
    meta = get_models_metadata()
    assert meta["status"] == "SUCCESS"
    assert len(meta["temporal_models"]) > 0
    assert len(meta["spatial_models"]) > 0
    assert len(meta["known_limitations"]) >= 1
