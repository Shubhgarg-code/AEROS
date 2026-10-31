"""Numerical Solvers for Atmospheric Advection-Diffusion Transport in AEROS.

Provides stable time-integration solvers for:
1. 2D Discrete Geospatial Grid Solver (Finite Difference Upwind + Central Diffusion)
2. Graph-Based Network Transport Solver (Directed Downwind Graph Message-Passing)
"""

import logging
from typing import Any, Dict, List, Optional, Tuple
import numpy as np

from aeros.physics.transport_equations import (
    compute_advection_diffusion_2d_step,
    compute_cfl_condition,
    meteorological_wind_to_uv,
)

logger = logging.getLogger("aeros.simulation.solver")


class Grid2DTransportSolver:
    """Solves 2D advection-diffusion-reaction equations across a discrete spatial grid."""

    def __init__(
        self,
        num_rows: int = 11,
        num_cols: int = 11,
        dx_km: float = 5.5,
        dy_km: float = 5.5,
        k_diff_km2h: float = 8.0,
        max_internal_dt_h: float = 0.05,
    ):
        self.num_rows = num_rows
        self.num_cols = num_cols
        self.dx_km = dx_km
        self.dy_km = dy_km
        self.k_diff_km2h = k_diff_km2h
        self.max_internal_dt_h = max_internal_dt_h

    def solve_step(
        self,
        current_field: np.ndarray,
        wind_speed_ms: float,
        wind_dir_deg: float,
        dt_output_h: float = 1.0,
        sources: Optional[np.ndarray] = None,
        sinks_lambda: Optional[np.ndarray] = None,
        rainfall_mm: float = 0.0,
    ) -> Tuple[np.ndarray, Dict[str, Any]]:
        """Advances concentration field by dt_output_h using adaptive CFL sub-stepping.
        
        Args:
            current_field: [rows, cols] concentration array (µg/m³).
            wind_speed_ms: Wind speed in meters per second.
            wind_dir_deg: Wind direction azimuth (degrees from North).
            dt_output_h: Desired output time interval in hours (default 1.0h).
            sources: [rows, cols] emission rate (µg/m³/h).
            sinks_lambda: [rows, cols] removal rate (1/h).
            rainfall_mm: Precipitation (scavenges aerosols).
            
        Returns:
            (next_field, step_diagnostics)
        """
        # Convert wind from m/s to km/h (1 m/s = 3.6 km/h)
        u_ms, v_ms = meteorological_wind_to_uv(wind_speed_ms, wind_dir_deg)
        u_kmh = u_ms * 3.6
        v_kmh = v_ms * 3.6

        # Atmospheric sink: dry deposition (~0.015 /h) + wet scavenging (0.04 * rain /h)
        base_lambda = 0.015 + 0.04 * max(0.0, rainfall_mm)
        if sinks_lambda is None:
            eff_sinks = np.full_like(current_field, base_lambda)
        else:
            eff_sinks = sinks_lambda + base_lambda

        # Check CFL condition and determine sub-step size
        cfl = compute_cfl_condition(u_kmh, v_kmh, self.k_diff_km2h, self.dx_km, self.dy_km, dt_output_h)
        max_dt = cfl["max_stable_dt_hours"]

        # Choose safe sub-step size
        target_sub_dt = min(self.max_internal_dt_h, max(1e-4, max_dt * 0.75))
        num_sub_steps = int(np.ceil(dt_output_h / target_sub_dt))
        sub_dt = dt_output_h / num_sub_steps

        state = current_field.copy()
        step_diag_history: List[Dict[str, float]] = []

        for _ in range(num_sub_steps):
            state, diag = compute_advection_diffusion_2d_step(
                c_field=state,
                u_kmh=u_kmh,
                v_kmh=v_kmh,
                k_diff_km2h=self.k_diff_km2h,
                dx_km=self.dx_km,
                dy_km=self.dy_km,
                dt_h=sub_dt,
                sources=sources,
                sinks_lambda=eff_sinks,
                boundary_mode="open",
            )
            step_diag_history.append(diag)

        # Aggregate diagnostics
        final_mass = float(np.sum(state) * self.dx_km * self.dy_km)
        initial_mass = float(np.sum(current_field) * self.dx_km * self.dy_km)
        total_source_added = float(
            sum(d["source_added_mass"] for d in step_diag_history)
        )
        total_sink_removed = float(
            sum(d["sink_removed_mass"] for d in step_diag_history)
        )

        overall_diagnostics = {
            "initial_mass": initial_mass,
            "final_mass": final_mass,
            "net_mass_change": final_mass - initial_mass,
            "total_source_added": total_source_added,
            "total_sink_removed": total_sink_removed,
            "cfl_advection": cfl["cfl_advection"],
            "diffusion_number": cfl["diffusion_number"],
            "num_sub_steps": num_sub_steps,
            "sub_dt_hours": sub_dt,
            "mean_concentration": float(np.mean(state)),
            "max_concentration": float(np.max(state)),
            "min_concentration": float(np.min(state)),
        }

        return state, overall_diagnostics


class GraphTransportSolver:
    """Solves mass-conservative network advection-diffusion across irregular station graphs."""

    def __init__(
        self,
        node_ids: List[str],
        coords: List[Tuple[float, float]],
        k_diff_scale: float = 0.05,
    ):
        self.node_ids = node_ids
        self.coords = coords
        self.num_nodes = len(node_ids)
        self.k_diff_scale = k_diff_scale

    def solve_step(
        self,
        current_node_c: np.ndarray,
        edge_index: np.ndarray,
        edge_attr: np.ndarray,
        dt_h: float = 1.0,
        sources: Optional[np.ndarray] = None,
        sinks_lambda: Optional[np.ndarray] = None,
        wind_speed_ms: float = 2.5,
    ) -> Tuple[np.ndarray, Dict[str, Any]]:
        """Advances node concentration values along graph edges.
        
        Args:
            current_node_c: [N] array of concentrations.
            edge_index: [2, E] array of directed source -> target edge connections.
            edge_attr: [E, 3] array of [distance_km, alignment, transport_weight].
            dt_h: Step duration (hours).
            sources: [N] emission rate (µg/m³/h).
            sinks_lambda: [N] removal rate (1/h).
            wind_speed_ms: Wind speed.
            
        Returns:
            (next_node_c, diagnostics)
        """
        N = self.num_nodes
        c_curr = current_node_c.copy()
        flux_in = np.zeros(N)
        flux_out = np.zeros(N)

        sources_idx = edge_index[0]
        targets_idx = edge_index[1]
        transport_weights = edge_attr[:, 2]

        # Scaled transfer rate per hour
        transfer_rate = transport_weights * 0.15

        for e in range(len(sources_idx)):
            u = sources_idx[e]
            v = targets_idx[e]
            w = transfer_rate[e]

            # Concentration gradient driving flux from u to v
            # If u is upwind of v, mass transfers from u to v
            delta_c = c_curr[u] - c_curr[v]
            if delta_c > 0:
                amount = w * delta_c * dt_h
                flux_out[u] += amount
                flux_in[v] += amount

        s_term = sources if sources is not None else np.zeros(N)
        l_term = (sinks_lambda if sinks_lambda is not None else np.full(N, 0.02)) * c_curr

        # Update concentrations
        c_next = c_curr + flux_in - flux_out + dt_h * (s_term - l_term)
        c_next = np.maximum(c_next, 0.0)

        diagnostics = {
            "initial_mean": float(np.mean(c_curr)),
            "final_mean": float(np.mean(c_next)),
            "max_concentration": float(np.max(c_next)),
            "total_flux_transferred": float(np.sum(flux_in)),
        }

        return c_next, diagnostics
