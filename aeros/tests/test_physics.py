"""Unit and Physics Verification Tests for AEROS Transport Equations.

Validates:
1. Meteorological wind speed/direction to zonal/meridional (u, v) decomposition.
2. Courant-Friedrichs-Lewy (CFL) advection & von Neumann diffusion stability metrics.
3. 2D Advection-Diffusion forward time-stepping and mass conservation.
4. Physics-Informed Transport Loss computation on tensor fields.
"""

import numpy as np
import pytest
import torch

from aeros.physics.physics_loss import PhysicsInformedTransportLoss
from aeros.physics.transport_equations import (
    compute_advection_diffusion_2d_step,
    compute_cfl_condition,
    meteorological_wind_to_uv,
)


def test_meteorological_wind_decomposition():
    """Verifies that wind directions produce physically correct Cartesian velocity vectors."""
    # North wind (0 deg): blows FROM North TOWARDS South -> u = 0, v < 0
    u, v = meteorological_wind_to_uv(wind_speed_ms=10.0, wind_dir_deg=0.0)
    assert abs(u) < 1e-4
    assert pytest.approx(v, abs=1e-4) == -10.0

    # East wind (90 deg): blows FROM East TOWARDS West -> u < 0, v = 0
    u, v = meteorological_wind_to_uv(wind_speed_ms=10.0, wind_dir_deg=90.0)
    assert pytest.approx(u, abs=1e-4) == -10.0
    assert abs(v) < 1e-4

    # South wind (180 deg): blows FROM South TOWARDS North -> u = 0, v > 0
    u, v = meteorological_wind_to_uv(wind_speed_ms=10.0, wind_dir_deg=180.0)
    assert abs(u) < 1e-4
    assert pytest.approx(v, abs=1e-4) == 10.0

    # West wind (270 deg): blows FROM West TOWARDS East -> u > 0, v = 0
    u, v = meteorological_wind_to_uv(wind_speed_ms=10.0, wind_dir_deg=270.0)
    assert pytest.approx(u, abs=1e-4) == 10.0
    assert abs(v) < 1e-4

    # Northwest wind (315 deg, typical Delhi winter): u > 0 (eastward), v < 0 (southward)
    u, v = meteorological_wind_to_uv(wind_speed_ms=10.0, wind_dir_deg=315.0)
    assert u > 0
    assert v < 0


def test_cfl_stability_condition():
    """Checks Courant-Friedrichs-Lewy stability evaluation under various grid/time scales."""
    # Stable configuration: small time step (0.05h = 3 min), moderate wind (10 km/h)
    stable_res = compute_cfl_condition(
        u_kmh=10.0,
        v_kmh=-10.0,
        k_diff_km2h=5.0,
        dx_km=5.0,
        dy_km=5.0,
        dt_h=0.05,
    )
    assert stable_res["is_stable"] is True
    assert stable_res["cfl_advection"] <= 1.0
    assert stable_res["diffusion_number"] <= 0.5
    assert stable_res["max_stable_dt_hours"] > 0

    # Unstable configuration: large time step (2.0h) with fast wind (40 km/h)
    unstable_res = compute_cfl_condition(
        u_kmh=40.0,
        v_kmh=-40.0,
        k_diff_km2h=20.0,
        dx_km=5.0,
        dy_km=5.0,
        dt_h=2.0,
    )
    assert unstable_res["is_stable"] is False
    assert unstable_res["cfl_advection"] > 1.0


def test_advection_diffusion_2d_step():
    """Verifies single step 2D transport, non-negativity preservation, and mass balance."""
    grid = np.zeros((11, 11), dtype=np.float32)
    # Inject a central point source pulse
    grid[5, 5] = 300.0

    # Advect with eastward wind (u > 0, v = 0)
    next_grid, diag = compute_advection_diffusion_2d_step(
        c_field=grid,
        u_kmh=15.0,
        v_kmh=0.0,
        k_diff_km2h=6.0,
        dx_km=5.0,
        dy_km=5.0,
        dt_h=0.05,
        sources=None,
        sinks_lambda=None,
        boundary_mode="open",
    )

    # 1. Non-negativity check
    assert np.all(next_grid >= 0.0)

    # 2. Diffusion check: peak should disperse from 300.0
    assert next_grid[5, 5] < 300.0

    # 3. Advection check: eastward neighbor (col 6) should receive concentration from (5, 5)
    assert next_grid[5, 6] > next_grid[5, 4]

    # 4. Mass conservation in interior before reaching open boundary
    assert pytest.approx(diag["initial_mass"], rel=1e-4) == diag["final_mass"]


def test_physics_informed_transport_loss():
    """Verifies that PhysicsInformedTransportLoss computes PDE residuals and penalizes non-negativity."""
    loss_module = PhysicsInformedTransportLoss(
        dx_km=5.0,
        dy_km=5.0,
        dt_h=1.0,
        default_k_diff=8.0,
    )

    # Synthetic concentration field: [Batch=1, Time=2, Height=7, Width=7]
    field_t0 = torch.full((1, 1, 7, 7), 100.0, dtype=torch.float32)
    field_t1 = torch.full((1, 1, 7, 7), 100.0, dtype=torch.float32)
    pred_c = torch.cat([field_t0, field_t1], dim=1)

    # Zero wind, no sources: uniform steady-state should have 0 spatial gradients
    u = torch.tensor([[0.0, 0.0]])
    v = torch.tensor([[0.0, 0.0]])

    total_loss, metrics = loss_module(pred_c, u, v)
    assert total_loss.item() >= 0.0
    assert metrics["loss_nonneg"] == 0.0
    assert metrics["loss_pde"] == pytest.approx(0.0, abs=1e-4)

    # Test non-negativity penalty on negative concentrations
    bad_pred_c = pred_c - 150.0  # Becomes -50.0
    _, bad_metrics = loss_module(bad_pred_c, u, v)
    assert bad_metrics["loss_nonneg"] > 0.0
