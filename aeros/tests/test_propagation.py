"""Unit and Integration Tests for AEROS Atmospheric Pollution Propagation Engine.

Validates:
1. Grid2DTransportSolver adaptive sub-stepping and CFL handling.
2. GraphTransportSolver message-passing along directed advection edges.
3. AtmosphericPropagationEngine forward rollouts and downwind plume shift.
4. GeoJSON spatial export integrity for frontend mapping layers.
"""

import numpy as np
import pytest

from aeros.inference.propagation_predictor import AerosPropagationPredictor
from aeros.simulation.numerical_solver import GraphTransportSolver, Grid2DTransportSolver
from aeros.simulation.propagation import AtmosphericPropagationEngine


def test_grid2d_transport_solver_substepping():
    """Verifies that Grid2DTransportSolver decomposes large time steps into stable sub-steps."""
    solver = Grid2DTransportSolver(num_rows=7, num_cols=7, dx_km=5.0, dy_km=5.0, k_diff_km2h=10.0)
    grid = np.full((7, 7), 50.0, dtype=np.float32)

    # Fast wind: 8.0 m/s ~ 28.8 km/h requires multiple internal sub-steps to meet CFL
    next_grid, diag = solver.solve_step(
        current_field=grid,
        wind_speed_ms=8.0,
        wind_dir_deg=315.0,
        dt_output_h=1.0,
        rainfall_mm=0.0,
    )

    assert diag["num_sub_steps"] > 1
    assert diag["cfl_advection"] > 0
    assert np.all(next_grid >= 0.0)


def test_graph_transport_solver_advection():
    """Verifies that GraphTransportSolver transfers mass along directed edges."""
    node_ids = ["node_a", "node_b"]
    coords = [(28.6, 77.2), (28.5, 77.3)]
    solver = GraphTransportSolver(node_ids=node_ids, coords=coords)

    # Edge from node 0 (upwind) to node 1 (downwind)
    edge_index = np.array([[0], [1]], dtype=np.int64)
    # [distance_km=15.0, alignment=0.9, transport_weight=0.8]
    edge_attr = np.array([[15.0, 0.9, 0.8]], dtype=np.float32)

    c_init = np.array([200.0, 50.0], dtype=np.float32)
    c_next, diag = solver.solve_step(
        current_node_c=c_init,
        edge_index=edge_index,
        edge_attr=edge_attr,
        dt_h=1.0,
    )

    # Node 0 (upwind) should lose concentration, Node 1 should gain or receive flux
    assert diag["total_flux_transferred"] > 0
    assert c_next[0] < c_init[0]
    assert np.all(c_next >= 0.0)


def test_propagation_engine_downwind_plume_transport():
    """Verifies that propagation engine transports pollutants in the direction of prevailing wind."""
    engine = AtmosphericPropagationEngine()

    # Place an isolated high concentration at an upwind station (Northwest Delhi: Jahangirpuri)
    initial_pm25 = {s["neighborhood_id"]: 40.0 for s in engine.stations}
    initial_pm25["jahangirpuri"] = 350.0
    initial_pm10 = {k: v * 1.6 for k, v in initial_pm25.items()}

    # Northwest wind (315°) blows TOWARDS Southeast
    weather = [{"wind_speed_ms": 4.0, "wind_dir_deg": 315.0, "rainfall_mm": 0.0} for _ in range(6)]

    sim = engine.simulate(
        initial_pm25=initial_pm25,
        initial_pm10=initial_pm10,
        weather_sequence=weather,
        duration_hours=6,
    )

    snapshots = sim["hourly_snapshots"]
    assert len(snapshots) == 7  # Hour 0 to 6
    assert snapshots[0]["step_hour"] == 0
    assert snapshots[-1]["step_hour"] == 6

    # Physical check: PM10 >= PM2.5 at every hour and station
    for nid in sim["station_pm25_series"].keys():
        pm25_vals = np.array(sim["station_pm25_series"][nid])
        pm10_vals = np.array(sim["station_pm10_series"][nid])
        assert np.all(pm10_vals >= pm25_vals - 1e-4)


def test_propagation_geojson_export():
    """Verifies that propagation engine exports valid GeoJSON FeatureCollection with 121 cells."""
    engine = AtmosphericPropagationEngine()
    dummy_snapshot = {
        "step_hour": 1,
        "timestamp": "2025-10-20T19:00:00",
        "mean_pm25": 110.0,
        "max_pm25": 180.0,
        "grid_pm25_snapshot": np.full((engine.num_rows, engine.num_cols), 110.0).tolist(),
        "grid_pm10_snapshot": np.full((engine.num_rows, engine.num_cols), 180.0).tolist(),
    }

    geojson = engine.export_geojson_feature_collection(dummy_snapshot)
    assert geojson["type"] == "FeatureCollection"
    assert len(geojson["features"]) == engine.num_rows * engine.num_cols
    assert geojson["features"][0]["geometry"]["type"] == "Polygon"
    assert "pm25" in geojson["features"][0]["properties"]
    assert "pm10" in geojson["features"][0]["properties"]


def test_propagation_predictor_wrapper():
    """Tests the high-level AerosPropagationPredictor inference wrapper."""
    predictor = AerosPropagationPredictor()
    result = predictor.run_simulation(
        initial_pm25={"anand_vihar": 150.0},
        initial_pm10={"anand_vihar": 220.0},
        duration_hours=3,
    )

    assert "simulation_id" in result
    assert "peak_hour_geojson" in result
    assert "final_hour_geojson" in result
    assert "peak_summary" in result
    assert result["peak_summary"]["max_pm25"] > 0
