"""Atmospheric Advection-Diffusion-Reaction Physics Engine for AEROS.

Implements fundamental fluid dynamics equations governing aerosol transport in the
planetary boundary layer (PBL):
    dC/dt + u · ∇C = ∇ · (K ∇C) + S - L

Where:
    - C(x, y, t): Pollutant concentration (PM2.5 or PM10 in µg/m³)
    - u = (u, v): Horizontal wind velocity vector (eastward u, northward v in m/s or km/h)
    - K: Atmospheric eddy diffusivity tensor/coefficient (km²/h or m²/s)
    - S(x, y, t): Emission source rate (µg/m³/h)
    - L(x, y, t): Deposition / atmospheric sink term = λ * C (dry deposition + wet scavenging)
"""

import logging
from typing import Any, Dict, Optional, Tuple
import numpy as np

logger = logging.getLogger("aeros.physics.transport")


def meteorological_wind_to_uv(wind_speed_ms: float, wind_dir_deg: float) -> Tuple[float, float]:
    """Converts standard meteorological wind speed and azimuth to zonal (u) and meridional (v) velocity.
    
    Meteorological convention:
        - wind_dir_deg is the direction the wind is blowing FROM (0° = North, 90° = East, 180° = South, 270° = West).
        - u (zonal, East-West): positive towards East.
        - v (meridional, North-South): positive towards North.
    
    Returns:
        (u, v) in m/s.
    """
    rad = np.radians(wind_dir_deg)
    # Wind blowing from North (0°) moves South (v < 0)
    # Wind blowing from West (270°) moves East (u > 0)
    u = -float(wind_speed_ms * np.sin(rad))
    v = -float(wind_speed_ms * np.cos(rad))
    return u, v


def compute_cfl_condition(
    u_kmh: float,
    v_kmh: float,
    k_diff_km2h: float,
    dx_km: float,
    dy_km: float,
    dt_h: float,
) -> Dict[str, Any]:
    """Computes Courant-Friedrichs-Lewy (CFL) advective and von Neumann diffusive stability metrics.
    
    Stability conditions:
        - Advective CFL: (|u| / dx + |v| / dy) * dt <= 1.0 (for explicit first-order upwind)
        - Diffusive Number: 2 * K * dt * (1/dx^2 + 1/dy^2) <= 0.5
    
    Returns:
        Dictionary containing cfl_advection, diffusion_number, is_stable, and max_stable_dt_h.
    """
    cfl_adv = (abs(u_kmh) / max(dx_km, 1e-4) + abs(v_kmh) / max(dy_km, 1e-4)) * dt_h
    diff_num = 2.0 * k_diff_km2h * dt_h * (1.0 / max(dx_km**2, 1e-4) + 1.0 / max(dy_km**2, 1e-4))

    # Calculate maximum permissible stable dt
    adv_denom = abs(u_kmh) / max(dx_km, 1e-4) + abs(v_kmh) / max(dy_km, 1e-4)
    dt_adv_max = 1.0 / adv_denom if adv_denom > 1e-5 else float("inf")

    diff_denom = 2.0 * k_diff_km2h * (1.0 / max(dx_km**2, 1e-4) + 1.0 / max(dy_km**2, 1e-4))
    dt_diff_max = 0.5 / diff_denom if diff_denom > 1e-5 else float("inf")

    max_stable_dt = min(dt_adv_max, dt_diff_max)
    is_stable = (cfl_adv <= 1.0) and (diff_num <= 0.5)

    return {
        "cfl_advection": float(round(cfl_adv, 4)),
        "diffusion_number": float(round(diff_num, 4)),
        "is_stable": bool(is_stable),
        "max_stable_dt_hours": float(round(max_stable_dt, 4)),
    }


def compute_advection_diffusion_2d_step(
    c_field: np.ndarray,
    u_kmh: float,
    v_kmh: float,
    k_diff_km2h: float,
    dx_km: float,
    dy_km: float,
    dt_h: float,
    sources: Optional[np.ndarray] = None,
    sinks_lambda: Optional[np.ndarray] = None,
    boundary_mode: str = "open",
) -> Tuple[np.ndarray, Dict[str, float]]:
    """Performs a single forward time step of 2D Advection-Diffusion-Reaction PDE using upwind differencing.
    
    Equation:
        C(t + dt) = C(t) + dt * [ - (u * dC/dx + v * dC/dy) + K * (d²C/dx² + d²C/dy²) + S - λ * C ]
    
    Grid index layout:
        - Axis 0 (rows): Latitude (South -> North or North -> South). By convention: row index i increases with Latitude (South to North).
        - Axis 1 (cols): Longitude (West -> East). Col index j increases with Longitude (West to East).
    
    Boundary condition:
        - "open": Outflow leaves domain, inflow sets gradient to 0 (extrapolated).
        - "periodic": Periodic wraparound.
        - "reflective": Neumann zero-flux at boundaries.
    
    Returns:
        (c_next, diagnostics_dict)
    """
    rows, cols = c_field.shape
    c_curr = c_field.copy()

    # Pre-allocate flux arrays
    dc_dx = np.zeros_like(c_curr)
    dc_dy = np.zeros_like(c_curr)
    d2c_dx2 = np.zeros_like(c_curr)
    d2c_dy2 = np.zeros_like(c_curr)

    # 1. Advection Spatial Discretization (Upwind Differencing Scheme)
    # Zonal Advection: u is eastward (column j increases)
    if u_kmh > 0:
        # Wind blowing West -> East: upstream is j-1
        dc_dx[:, 1:] = (c_curr[:, 1:] - c_curr[:, :-1]) / dx_km
        if boundary_mode == "open":
            dc_dx[:, 0] = 0.0  # Inflow boundary
        else:
            dc_dx[:, 0] = (c_curr[:, 0] - c_curr[:, -1]) / dx_km
    elif u_kmh < 0:
        # Wind blowing East -> West: upstream is j+1
        dc_dx[:, :-1] = (c_curr[:, 1:] - c_curr[:, :-1]) / dx_km
        if boundary_mode == "open":
            dc_dx[:, -1] = 0.0  # Inflow boundary
        else:
            dc_dx[:, -1] = (c_curr[:, 0] - c_curr[:, -1]) / dx_km

    # Meridional Advection: v is northward (row i increases)
    if v_kmh > 0:
        # Wind blowing South -> North: upstream is i-1
        dc_dy[1:, :] = (c_curr[1:, :] - c_curr[:-1, :]) / dy_km
        if boundary_mode == "open":
            dc_dy[0, :] = 0.0
        else:
            dc_dy[0, :] = (c_curr[0, :] - c_curr[-1, :]) / dy_km
    elif v_kmh < 0:
        # Wind blowing North -> South: upstream is i+1
        dc_dy[:-1, :] = (c_curr[1:, :] - c_curr[:-1, :]) / dy_km
        if boundary_mode == "open":
            dc_dy[-1, :] = 0.0
        else:
            dc_dy[-1, :] = (c_curr[0, :] - c_curr[-1, :]) / dy_km

    # 2. Diffusion Spatial Discretization (Central Differencing Scheme)
    # d²C/dx²
    d2c_dx2[:, 1:-1] = (c_curr[:, 2:] - 2.0 * c_curr[:, 1:-1] + c_curr[:, :-2]) / (dx_km**2)
    # Boundaries for diffusion
    d2c_dx2[:, 0] = (c_curr[:, 1] - c_curr[:, 0]) / (dx_km**2)
    d2c_dx2[:, -1] = (c_curr[:, -2] - c_curr[:, -1]) / (dx_km**2)

    # d²C/dy²
    d2c_dy2[1:-1, :] = (c_curr[2:, :] - 2.0 * c_curr[1:-1, :] + c_curr[:-2, :]) / (dy_km**2)
    d2c_dy2[0, :] = (c_curr[1, :] - c_curr[0, :]) / (dy_km**2)
    d2c_dy2[-1, :] = (c_curr[-2, :] - c_curr[-1, :]) / (dy_km**2)

    # 3. Source and Sink terms
    s_term = sources if sources is not None else np.zeros_like(c_curr)
    if sinks_lambda is not None:
        l_term = sinks_lambda * c_curr
    else:
        l_term = np.zeros_like(c_curr)

    # 4. Time Integration (Forward Euler)
    advection_flux = -(u_kmh * dc_dx + v_kmh * dc_dy)
    diffusion_flux = k_diff_km2h * (d2c_dx2 + d2c_dy2)
    net_rate = advection_flux + diffusion_flux + s_term - l_term

    c_next = c_curr + dt_h * net_rate

    # Physical enforcement: concentrations cannot become negative
    c_next = np.maximum(c_next, 0.0)

    # Mass conservation diagnostic
    initial_mass = float(np.sum(c_curr) * dx_km * dy_km)
    final_mass = float(np.sum(c_next) * dx_km * dy_km)
    total_source_mass = float(np.sum(s_term) * dx_km * dy_km * dt_h)
    total_sink_mass = float(np.sum(l_term) * dx_km * dy_km * dt_h)

    diagnostics = {
        "initial_mass": initial_mass,
        "final_mass": final_mass,
        "mass_delta": final_mass - initial_mass,
        "source_added_mass": total_source_mass,
        "sink_removed_mass": total_sink_mass,
        "mean_concentration": float(np.mean(c_next)),
        "max_concentration": float(np.max(c_next)),
    }

    return c_next, diagnostics
