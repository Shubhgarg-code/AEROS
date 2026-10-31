"""Diwali What-If Counterfactual Simulation Engine for AEROS.

Executes physical simulations of policy interventions, emission spikes,
and meteorological ventilation scenarios during episodic Diwali pollution events.
"""

from datetime import datetime, timedelta
import logging
from typing import Any, Dict, List, Optional
import numpy as np

from aeros.ingestion.cpcb import get_cpcb_stations
from aeros.simulation.propagation import AtmosphericPropagationEngine
from aeros.simulation.scenarios import (
    SCENARIO_REGISTRY,
    ScenarioConfig,
    ScenarioType,
    compute_diurnal_traffic_profile,
    compute_firecracker_emission_pulse,
)

logger = logging.getLogger("aeros.simulation.counterfactual")


class DiwaliWhatIfSimulator:
    """Counterfactual simulator comparing policy and environmental scenarios."""

    def __init__(
        self,
        propagation_engine: Optional[AtmosphericPropagationEngine] = None,
    ):
        self.engine = propagation_engine or AtmosphericPropagationEngine()
        self.stations = get_cpcb_stations()

    def _generate_scenario_inputs(
        self,
        config: ScenarioConfig,
        start_time: datetime,
        diwali_night_start: datetime,
        duration_hours: int,
        base_weather: Optional[List[Dict[str, float]]] = None,
    ) -> Tuple[List[Dict[str, float]], List[np.ndarray]]:
        """Constructs meteorological sequence and gridded emission inputs for the scenario."""
        weather_seq = []
        emission_seq = []

        for h in range(duration_hours):
            current_time = start_time + timedelta(hours=h)
            hour_of_day = current_time.hour

            # Base weather
            if base_weather and h < len(base_weather):
                bw = base_weather[h]
                ws = float(bw.get("wind_speed_ms", 2.2))
                wd = float(bw.get("wind_dir_deg", 315.0))
                rain = float(bw.get("rainfall_mm", 0.0))
            else:
                ws = 2.2
                wd = 315.0
                rain = 0.0

            # Perturb weather per scenario
            mod_ws = max(0.5, ws + config.wind_speed_delta_ms)
            mod_rain = max(0.0, rain + config.rainfall_delta_mm)

            weather_seq.append({
                "wind_speed_ms": mod_ws,
                "wind_dir_deg": wd,
                "rainfall_mm": mod_rain,
            })

            # Calculate relative hour from Diwali night start (18:00 on Diwali day)
            rel_hour = (current_time - diwali_night_start).total_seconds() / 3600.0

            # 1. Background emission rate (~2.5 µg/m³/h)
            s_bg = 2.5 * self.engine.emission_weight_grid

            # 2. Diurnal vehicular traffic emissions (~3.0 µg/m³/h base * diurnal factor * multiplier)
            traffic_diurnal = compute_diurnal_traffic_profile(hour_of_day)
            s_traffic = 3.0 * traffic_diurnal * config.traffic_multiplier * self.engine.emission_weight_grid

            # 3. Episodic pyrotechnic pulse
            pulse_pm25, _ = compute_firecracker_emission_pulse(rel_hour, base_amplitude_pm25=55.0)
            s_firecracker = pulse_pm25 * config.firecracker_multiplier * self.engine.emission_weight_grid

            # Combined PM2.5 hourly emission grid
            s_total = s_bg + s_traffic + s_firecracker
            emission_seq.append(s_total)

        return weather_seq, emission_seq

    def simulate_scenario(
        self,
        scenario_type: ScenarioType,
        initial_pm25: Optional[Dict[str, float]] = None,
        initial_pm10: Optional[Dict[str, float]] = None,
        start_time_iso: str = "2025-10-19T18:00:00",
        diwali_night_iso: str = "2025-10-20T18:00:00",
        duration_hours: int = 72,
        base_weather: Optional[List[Dict[str, float]]] = None,
    ) -> Dict[str, Any]:
        """Runs a single counterfactual scenario rollout and calculates summary exposure metrics."""
        config = SCENARIO_REGISTRY[scenario_type]
        t_start = datetime.fromisoformat(start_time_iso)
        t_diwali = datetime.fromisoformat(diwali_night_iso)

        # Default initial conditions if not provided
        if initial_pm25 is None:
            initial_pm25 = {s["neighborhood_id"]: 85.0 for s in self.stations}
        if initial_pm10 is None:
            initial_pm10 = {s["neighborhood_id"]: 150.0 for s in self.stations}

        weather_seq, emission_seq = self._generate_scenario_inputs(
            config=config,
            start_time=t_start,
            diwali_night_start=t_diwali,
            duration_hours=duration_hours,
            base_weather=base_weather,
        )

        sim_output = self.engine.simulate(
            initial_pm25=initial_pm25,
            initial_pm10=initial_pm10,
            weather_sequence=weather_seq,
            emission_sources_sequence=emission_seq,
            duration_hours=duration_hours,
            start_time_iso=start_time_iso,
        )

        snapshots = sim_output["hourly_snapshots"]
        pm25_means = [s["mean_pm25"] for s in snapshots]
        pm10_means = [s["mean_pm10"] for s in snapshots]
        pm25_maxs = [s["max_pm25"] for s in snapshots]

        peak_idx = int(np.argmax(pm25_means))
        peak_hour = snapshots[peak_idx]["step_hour"]
        peak_timestamp = snapshots[peak_idx]["timestamp"]
        peak_pm25 = float(pm25_means[peak_idx])
        peak_pm10 = float(pm10_means[peak_idx])
        max_hotspot_pm25 = float(max(pm25_maxs))

        # Cumulative exposure (area under concentration curve in µg·h/m³)
        trapz_func = getattr(np, "trapezoid", getattr(np, "trapz", None))
        if trapz_func is not None:
            cumulative_exposure_pm25 = float(trapz_func(pm25_means))
            cumulative_exposure_pm10 = float(trapz_func(pm10_means))
        else:
            cumulative_exposure_pm25 = float(np.sum(pm25_means))
            cumulative_exposure_pm10 = float(np.sum(pm10_means))

        # Exceedance hours
        exceed_pm25_60 = int(sum(1 for val in pm25_means if val > 60.0))
        exceed_pm25_250 = int(sum(1 for val in pm25_means if val > 250.0))
        exceed_pm10_100 = int(sum(1 for val in pm10_means if val > 100.0))

        # Population-weighted exposure index proxy using road density factors
        weights = [s.get("road_density_factor", 1.0) for s in self.stations]
        total_w = sum(weights)
        st_series = sim_output["station_pm25_series"]
        weighted_curve = np.zeros(len(snapshots))
        for i, s in enumerate(self.stations):
            w = weights[i]
            vals = np.array(st_series[s["neighborhood_id"]])
            weighted_curve += w * vals
        weighted_curve /= total_w
        pop_weighted_index = float(round(float(np.mean(weighted_curve)), 2))

        return {
            "scenario_type": scenario_type.value,
            "scenario_name": config.name,
            "description": config.description,
            "start_time": start_time_iso,
            "duration_hours": duration_hours,
            "peak_pm25": round(peak_pm25, 2),
            "peak_pm10": round(peak_pm10, 2),
            "max_hotspot_pm25": round(max_hotspot_pm25, 2),
            "peak_hour": peak_hour,
            "peak_timestamp": peak_timestamp,
            "cumulative_exposure_pm25": round(cumulative_exposure_pm25, 2),
            "cumulative_exposure_pm10": round(cumulative_exposure_pm10, 2),
            "exceedance_hours_pm25_60": exceed_pm25_60,
            "exceedance_hours_pm25_250": exceed_pm25_250,
            "exceedance_hours_pm10_100": exceed_pm10_100,
            "population_weighted_exposure_index": pop_weighted_index,
            "hourly_mean_pm25_series": [round(x, 2) for x in pm25_means],
            "hourly_mean_pm10_series": [round(x, 2) for x in pm10_means],
            "timestamps": sim_output["timestamps"],
            "station_pm25_series": sim_output["station_pm25_series"],
        }

    def compare_all_scenarios(
        self,
        scenarios: Optional[List[ScenarioType]] = None,
        initial_pm25: Optional[Dict[str, float]] = None,
        initial_pm10: Optional[Dict[str, float]] = None,
        start_time_iso: str = "2025-10-19T18:00:00",
        diwali_night_iso: str = "2025-10-20T18:00:00",
        duration_hours: int = 72,
    ) -> Dict[str, Any]:
        """Runs batch simulation across multiple scenarios and benchmarks against baseline."""
        if scenarios is None:
            scenarios = list(ScenarioType)

        # Ensure BASELINE is evaluated first to serve as reference
        if ScenarioType.BASELINE not in scenarios:
            scenarios = [ScenarioType.BASELINE] + scenarios

        scenario_results: Dict[str, Dict[str, Any]] = {}
        for sc in scenarios:
            logger.info("Executing counterfactual scenario: %s", sc.value)
            res = self.simulate_scenario(
                scenario_type=sc,
                initial_pm25=initial_pm25,
                initial_pm10=initial_pm10,
                start_time_iso=start_time_iso,
                diwali_night_iso=diwali_night_iso,
                duration_hours=duration_hours,
            )
            scenario_results[sc.value] = res

        baseline_res = scenario_results[ScenarioType.BASELINE.value]
        base_peak_pm25 = baseline_res["peak_pm25"]
        base_cum_exp = baseline_res["cumulative_exposure_pm25"]
        base_peak_hour = baseline_res["peak_hour"]

        comparison_table = []
        for sc in scenarios:
            r = scenario_results[sc.value]
            delta_peak = float(round(r["peak_pm25"] - base_peak_pm25, 2))
            delta_peak_pct = float(round((delta_peak / max(base_peak_pm25, 1e-4)) * 100.0, 2))
            delta_cum = float(round(r["cumulative_exposure_pm25"] - base_cum_exp, 2))
            delta_cum_pct = float(round((delta_cum / max(base_cum_exp, 1e-4)) * 100.0, 2))
            time_shift_hours = r["peak_hour"] - base_peak_hour

            comparison_table.append({
                "scenario_type": sc.value,
                "scenario_name": r["scenario_name"],
                "peak_pm25": r["peak_pm25"],
                "delta_peak_pm25": delta_peak,
                "delta_peak_pct": delta_peak_pct,
                "time_to_peak_hours": r["peak_hour"],
                "peak_shift_hours": time_shift_hours,
                "cumulative_exposure_pm25": r["cumulative_exposure_pm25"],
                "delta_cumulative_exposure_pct": delta_cum_pct,
                "exceedance_hours_pm25_60": r["exceedance_hours_pm25_60"],
                "population_weighted_exposure_index": r["population_weighted_exposure_index"],
            })

        return {
            "reference_scenario": ScenarioType.BASELINE.value,
            "duration_hours": duration_hours,
            "baseline_peak_pm25": base_peak_pm25,
            "baseline_cumulative_pm25": base_cum_exp,
            "comparison_table": comparison_table,
            "scenario_details": scenario_results,
        }
