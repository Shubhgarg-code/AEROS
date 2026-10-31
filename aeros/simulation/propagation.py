"""Atmospheric Pollution Propagation Engine for AEROS.

Simulates the spatial evolution and transport of particulate matter (PM2.5 and PM10)
across Delhi NCR over forward forecasting horizons (1h to 72h). Integrates numerical
advection-diffusion dynamics, road density emission proxies, and meteorological forcing.
"""

from datetime import datetime, timedelta
import logging
from typing import Any, Dict, List, Optional, Tuple
import numpy as np

from aeros.ingestion.cpcb import get_cpcb_stations
from aeros.ingestion.geospatial import haversine_distance_km
from aeros.simulation.numerical_solver import Grid2DTransportSolver
from aeros.spatial.distance_features import compute_idw_weights
from aeros.spatial.grid_generator import DelhiGeospatialGrid

logger = logging.getLogger("aeros.simulation.propagation")


class AtmosphericPropagationEngine:
    """Simulates 2D physical transport and dispersion of air pollution over Delhi NCR."""

    def __init__(
        self,
        grid_resolution_deg: float = 0.05,
        k_diff_km2h: float = 8.0,
    ):
        self.grid = DelhiGeospatialGrid(resolution_deg=grid_resolution_deg)
        self.num_rows = self.grid.num_rows
        self.num_cols = self.grid.num_cols
        self.stations = get_cpcb_stations()
        self.station_coords = [(s["latitude"], s["longitude"]) for s in self.stations]

        # Resolution in kilometers: 0.05 deg latitude ~ 5.55 km; 0.05 deg lon at 28.6N ~ 4.87 km
        self.dx_km = 4.87
        self.dy_km = 5.55
        self.solver = Grid2DTransportSolver(
            num_rows=self.num_rows,
            num_cols=self.num_cols,
            dx_km=self.dx_km,
            dy_km=self.dy_km,
            k_diff_km2h=k_diff_km2h,
        )

        # Precompute grid cell centroids and road density / emission weights
        self._init_spatial_emission_weights()

    def _init_spatial_emission_weights(self) -> None:
        """Computes spatial emission intensity matrix based on road densities and station metadata."""
        self.emission_weight_grid = np.ones((self.num_rows, self.num_cols), dtype=np.float32)

        for cell in self.grid.grid_cells:
            r = cell["row"]
            c = cell["col"]
            # Check if cell has physical monitoring stations with known road density
            contained = cell.get("monitoring_stations", [])
            if contained:
                st_meta = next((s for s in self.stations if s["neighborhood_id"] in contained), None)
                if st_meta:
                    self.emission_weight_grid[r, c] = float(st_meta.get("road_density_factor", 1.2))
            else:
                # Modulate slightly by distance to city center (Connaught Place ~ 28.63°N, 77.22°E)
                center_dist = haversine_distance_km(cell["centroid_lat"], cell["centroid_lon"], 28.63, 77.22)
                urban_decay = float(np.exp(-center_dist / 18.0))
                self.emission_weight_grid[r, c] = 0.8 + 0.6 * urban_decay

    def stations_to_grid(self, station_values: Dict[str, float], default_val: float = 90.0) -> np.ndarray:
        """Interpolates discrete station measurements onto the 2D spatial grid via Inverse Distance Weighting."""
        grid_field = np.zeros((self.num_rows, self.num_cols), dtype=np.float32)

        # Assemble values corresponding to self.station_coords
        vals = np.array([
            station_values.get(s["neighborhood_id"], default_val)
            for s in self.stations
        ], dtype=np.float32)

        for cell in self.grid.grid_cells:
            r = cell["row"]
            c = cell["col"]
            pt = (cell["centroid_lat"], cell["centroid_lon"])
            w = compute_idw_weights(pt, self.station_coords, power=2.0)
            grid_field[r, c] = float(np.sum(w * vals))

        return grid_field

    def grid_to_stations(self, grid_field: np.ndarray) -> Dict[str, float]:
        """Samples the 2D concentration grid at physical monitoring station coordinates."""
        station_estimates = {}
        for s in self.stations:
            lat = s["latitude"]
            lon = s["longitude"]
            # Find closest cell
            r = int(np.clip(
                int(round((lat - self.grid.bounds["lat_min"]) / self.grid.resolution)),
                0,
                self.num_rows - 1,
            ))
            c = int(np.clip(
                int(round((lon - self.grid.bounds["lon_min"]) / self.grid.resolution)),
                0,
                self.num_cols - 1,
            ))
            station_estimates[s["neighborhood_id"]] = float(grid_field[r, c])
        return station_estimates

    def simulate(
        self,
        initial_pm25: Dict[str, float],
        initial_pm10: Dict[str, float],
        weather_sequence: Optional[List[Dict[str, float]]] = None,
        emission_sources_sequence: Optional[List[np.ndarray]] = None,
        duration_hours: int = 24,
        start_time_iso: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Runs multi-hour 2D forward advection-diffusion propagation simulation.
        
        Args:
            initial_pm25: Initial PM2.5 by station ID.
            initial_pm10: Initial PM10 by station ID.
            weather_sequence: Optional list of dicts with keys 'wind_speed_ms', 'wind_dir_deg', 'rainfall_mm'.
            emission_sources_sequence: Optional list of [rows, cols] emission source matrices per hour.
            duration_hours: Number of forward hours to simulate (default 24).
            start_time_iso: Starting ISO timestamp.
            
        Returns:
            Dictionary containing hourly simulation snapshots, station time series, and mass conservation report.
        """
        # Interpolate initial conditions to 2D grids
        c_pm25 = self.stations_to_grid(initial_pm25, default_val=90.0)
        c_pm10 = self.stations_to_grid(initial_pm10, default_val=160.0)

        # Baseline weather if not provided (typical Delhi winter NW wind ~ 2.5 m/s, 315 deg)
        if weather_sequence is None:
            weather_sequence = [
                {"wind_speed_ms": 2.5, "wind_dir_deg": 315.0, "rainfall_mm": 0.0}
                for _ in range(duration_hours)
            ]
        elif len(weather_sequence) < duration_hours:
            # Pad with last known weather
            last_w = weather_sequence[-1]
            weather_sequence = weather_sequence + [last_w] * (duration_hours - len(weather_sequence))

        t0 = datetime.fromisoformat(start_time_iso) if start_time_iso else datetime(2025, 10, 20, 18, 0, 0)

        hourly_snapshots = []
        station_pm25_series: Dict[str, List[float]] = {s["neighborhood_id"]: [] for s in self.stations}
        station_pm10_series: Dict[str, List[float]] = {s["neighborhood_id"]: [] for s in self.stations}
        timestamps = []

        total_mass_initial_pm25 = float(np.sum(c_pm25) * self.dx_km * self.dy_km)
        total_mass_initial_pm10 = float(np.sum(c_pm10) * self.dx_km * self.dy_km)

        # Record step 0 (initial state)
        st_pm25_curr = self.grid_to_stations(c_pm25)
        st_pm10_curr = self.grid_to_stations(c_pm10)
        t_str = t0.isoformat()
        timestamps.append(t_str)
        for nid, val in st_pm25_curr.items():
            station_pm25_series[nid].append(round(val, 2))
        for nid, val in st_pm10_curr.items():
            station_pm10_series[nid].append(round(val, 2))

        hourly_snapshots.append({
            "step_hour": 0,
            "timestamp": t_str,
            "mean_pm25": float(round(np.mean(c_pm25), 2)),
            "max_pm25": float(round(np.max(c_pm25), 2)),
            "mean_pm10": float(round(np.mean(c_pm10), 2)),
            "max_pm10": float(round(np.max(c_pm10), 2)),
            "wind_speed_ms": weather_sequence[0].get("wind_speed_ms", 2.5),
            "wind_dir_deg": weather_sequence[0].get("wind_dir_deg", 315.0),
            "grid_pm25_snapshot": c_pm25.round(2).tolist(),
            "grid_pm10_snapshot": c_pm10.round(2).tolist(),
        })

        # Advance hour by hour
        for step in range(duration_hours):
            w = weather_sequence[step]
            ws = float(w.get("wind_speed_ms", 2.5))
            wd = float(w.get("wind_dir_deg", 315.0))
            rain = float(w.get("rainfall_mm", 0.0))

            # Emission term for PM2.5 and PM10
            if emission_sources_sequence and step < len(emission_sources_sequence):
                s_pm25 = emission_sources_sequence[step]
                s_pm10 = s_pm25 * 1.5
            else:
                # Default baseline background emissions
                s_pm25 = self.emission_weight_grid * 3.5  # ~ 3.5 µg/m³/h base
                s_pm10 = self.emission_weight_grid * 6.0

            # Advance PM2.5
            c_pm25, diag_pm25 = self.solver.solve_step(
                current_field=c_pm25,
                wind_speed_ms=ws,
                wind_dir_deg=wd,
                dt_output_h=1.0,
                sources=s_pm25,
                rainfall_mm=rain,
            )

            # Advance PM10
            c_pm10, diag_pm10 = self.solver.solve_step(
                current_field=c_pm10,
                wind_speed_ms=ws,
                wind_dir_deg=wd,
                dt_output_h=1.0,
                sources=s_pm10,
                rainfall_mm=rain,
            )

            # Enforce physical rule: PM10 >= PM2.5
            c_pm10 = np.maximum(c_pm10, c_pm25)

            curr_time = t0 + timedelta(hours=step + 1)
            t_curr_str = curr_time.isoformat()
            timestamps.append(t_curr_str)

            # Sample station estimates
            st_25 = self.grid_to_stations(c_pm25)
            st_10 = self.grid_to_stations(c_pm10)
            for nid, val in st_25.items():
                station_pm25_series[nid].append(round(val, 2))
            for nid, val in st_10.items():
                station_pm10_series[nid].append(round(val, 2))

            hourly_snapshots.append({
                "step_hour": step + 1,
                "timestamp": t_curr_str,
                "mean_pm25": float(round(np.mean(c_pm25), 2)),
                "max_pm25": float(round(np.max(c_pm25), 2)),
                "mean_pm10": float(round(np.mean(c_pm10), 2)),
                "max_pm10": float(round(np.max(c_pm10), 2)),
                "wind_speed_ms": ws,
                "wind_dir_deg": wd,
                "grid_pm25_snapshot": c_pm25.round(2).tolist(),
                "grid_pm10_snapshot": c_pm10.round(2).tolist(),
            })

        final_mass_pm25 = float(np.sum(c_pm25) * self.dx_km * self.dy_km)
        final_mass_pm10 = float(np.sum(c_pm10) * self.dx_km * self.dy_km)

        return {
            "simulation_id": f"prop_sim_{int(t0.timestamp())}",
            "start_time": t0.isoformat(),
            "duration_hours": duration_hours,
            "grid_dimensions": {"rows": self.num_rows, "cols": self.num_cols, "dx_km": self.dx_km, "dy_km": self.dy_km},
            "timestamps": timestamps,
            "hourly_snapshots": hourly_snapshots,
            "station_pm25_series": station_pm25_series,
            "station_pm10_series": station_pm10_series,
            "mass_diagnostics": {
                "initial_pm25_mass_kg": round(total_mass_initial_pm25 * 1e-6, 3),
                "final_pm25_mass_kg": round(final_mass_pm25 * 1e-6, 3),
                "initial_pm10_mass_kg": round(total_mass_initial_pm10 * 1e-6, 3),
                "final_pm10_mass_kg": round(final_mass_pm10 * 1e-6, 3),
            },
        }

    def export_geojson_feature_collection(self, snapshot: Dict[str, Any]) -> Dict[str, Any]:
        """Exports a single hourly grid snapshot as a valid GeoJSON FeatureCollection."""
        grid_pm25 = np.array(snapshot["grid_pm25_snapshot"])
        grid_pm10 = np.array(snapshot["grid_pm10_snapshot"])
        features = []

        for cell in self.grid.grid_cells:
            r = cell["row"]
            c = cell["col"]
            bbox = cell["bbox"]
            pm25_val = float(grid_pm25[r, c])
            pm10_val = float(grid_pm10[r, c])

            polygon_coords = [
                [bbox["lon_west"], bbox["lat_south"]],
                [bbox["lon_east"], bbox["lat_south"]],
                [bbox["lon_east"], bbox["lat_north"]],
                [bbox["lon_west"], bbox["lat_north"]],
                [bbox["lon_west"], bbox["lat_south"]],
            ]

            feature = {
                "type": "Feature",
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [polygon_coords],
                },
                "properties": {
                    "cell_id": cell["cell_id"],
                    "centroid_lat": cell["centroid_lat"],
                    "centroid_lon": cell["centroid_lon"],
                    "pm25": pm25_val,
                    "pm10": pm10_val,
                    "is_monitored": cell["is_monitored"],
                    "step_hour": snapshot["step_hour"],
                    "timestamp": snapshot["timestamp"],
                },
            }
            features.append(feature)

        return {
            "type": "FeatureCollection",
            "features": features,
            "properties": {
                "timestamp": snapshot["timestamp"],
                "step_hour": snapshot["step_hour"],
                "mean_pm25": snapshot["mean_pm25"],
                "max_pm25": snapshot["max_pm25"],
            },
        }
