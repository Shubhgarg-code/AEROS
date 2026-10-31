"""Inference interface for Atmospheric Pollution Propagation Engine."""

from typing import Any, Dict, List, Optional
from aeros.simulation.propagation import AtmosphericPropagationEngine


class AerosPropagationPredictor:
    """Production serving wrapper for running spatial propagation simulations."""

    def __init__(self):
        self.engine = AtmosphericPropagationEngine()

    def run_simulation(
        self,
        initial_pm25: Dict[str, float],
        initial_pm10: Dict[str, float],
        weather_sequence: Optional[List[Dict[str, float]]] = None,
        duration_hours: int = 24,
        start_time_iso: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Runs propagation rollout and includes GeoJSON export for the final and peak hours."""
        sim_results = self.engine.simulate(
            initial_pm25=initial_pm25,
            initial_pm10=initial_pm10,
            weather_sequence=weather_sequence,
            duration_hours=duration_hours,
            start_time_iso=start_time_iso,
        )

        # Generate GeoJSON for peak snapshot and final snapshot
        snapshots = sim_results["hourly_snapshots"]
        peak_idx = int(max(range(len(snapshots)), key=lambda i: snapshots[i]["max_pm25"]))

        peak_geojson = self.engine.export_geojson_feature_collection(snapshots[peak_idx])
        final_geojson = self.engine.export_geojson_feature_collection(snapshots[-1])

        sim_results["peak_hour_geojson"] = peak_geojson
        sim_results["final_hour_geojson"] = final_geojson
        sim_results["peak_summary"] = {
            "peak_hour": snapshots[peak_idx]["step_hour"],
            "peak_timestamp": snapshots[peak_idx]["timestamp"],
            "max_pm25": snapshots[peak_idx]["max_pm25"],
            "mean_pm25": snapshots[peak_idx]["mean_pm25"],
        }

        return sim_results
