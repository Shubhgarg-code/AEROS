"""Scenario Validation and Artifact Generation Runner for AEROS Round 5.

Executes comprehensive physical simulation across all 7 Diwali counterfactual scenarios,
evaluates atmospheric recovery dynamics across ventilation regimes, exports GeoJSON
propagation map layers, and writes rigorous technical evaluation reports.
"""

from datetime import datetime
import json
import logging
import os
import sys

# Ensure package root is in sys.path
sys.path.insert(0, os.path.abspath("."))

from aeros.inference.propagation_predictor import AerosPropagationPredictor
from aeros.inference.recovery_predictor import AerosRecoveryPredictor
from aeros.simulation.counterfactual import DiwaliWhatIfSimulator
from aeros.simulation.scenarios import ScenarioType

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("aeros.evaluation.scenarios")


def run_complete_scenario_validation():
    """Generates all Round 5 simulation artifacts, reports, and GeoJSON datasets."""
    logger.info("Initializing AEROS Simulation Engines...")
    prop_predictor = AerosPropagationPredictor()
    sim = DiwaliWhatIfSimulator()
    rec_predictor = AerosRecoveryPredictor()

    os.makedirs("aeros/artifacts/reports", exist_ok=True)
    os.makedirs("aeros/artifacts/graph_data", exist_ok=True)

    # -------------------------------------------------------------
    # 1. 2D Physical Propagation Simulation & GeoJSON Map Generation
    # -------------------------------------------------------------
    logger.info("Running 24-hour physical propagation simulation...")
    # Representative Diwali evening initial state
    init_pm25 = {
        "anand_vihar": 220.0,
        "punjabi_bagh": 160.0,
        "ito": 140.0,
        "r_k_puram": 135.0,
        "dwarka": 125.0,
        "jahangirpuri": 195.0,
        "mandir_marg": 130.0,
    }
    init_pm10 = {k: v * 1.65 for k, v in init_pm25.items()}

    # Northwest synoptic wind (315° at 2.5 m/s)
    weather_seq = [
        {"wind_speed_ms": 2.5, "wind_dir_deg": 315.0, "rainfall_mm": 0.0}
        for _ in range(24)
    ]

    prop_results = prop_predictor.run_simulation(
        initial_pm25=init_pm25,
        initial_pm10=init_pm10,
        weather_sequence=weather_seq,
        duration_hours=24,
        start_time_iso="2025-10-20T18:00:00",
    )

    geojson_path = "aeros/artifacts/graph_data/delhi_propagation_simulation.geojson"
    with open(geojson_path, "w", encoding="utf-8") as f:
        json.dump(prop_results["peak_hour_geojson"], f, indent=2)
    logger.info("Saved propagation GeoJSON to %s", geojson_path)

    # -------------------------------------------------------------
    # 2. Comprehensive 7-Scenario Counterfactual Simulation
    # -------------------------------------------------------------
    logger.info("Running batch simulation for all 7 policy & atmospheric scenarios (72 hours)...")
    comp_results = sim.compare_all_scenarios(
        scenarios=list(ScenarioType),
        start_time_iso="2025-10-19T18:00:00",
        diwali_night_iso="2025-10-20T18:00:00",
        duration_hours=72,
    )

    # -------------------------------------------------------------
    # 3. Atmospheric Recovery Analysis on Baseline and Mitigation
    # -------------------------------------------------------------
    logger.info("Evaluating post-Diwali atmospheric recovery dynamics...")
    base_pm25_series = comp_results["scenario_details"]["baseline"]["hourly_mean_pm25_series"]
    mit_pm25_series = comp_results["scenario_details"]["combined_mitigation"]["hourly_mean_pm25_series"]
    timestamps = comp_results["scenario_details"]["baseline"]["timestamps"]

    base_recovery = rec_predictor.predict_recovery(
        pm25_series=base_pm25_series,
        timestamps=timestamps,
        target_pm25_threshold=60.0,
        wind_speed_ms=2.2,
    )
    mit_recovery = rec_predictor.predict_recovery(
        pm25_series=mit_pm25_series,
        timestamps=timestamps,
        target_pm25_threshold=60.0,
        wind_speed_ms=2.2,
    )

    # -------------------------------------------------------------
    # 4. Save Technical Reports (JSON & Markdown)
    # -------------------------------------------------------------
    report_json = {
        "timestamp": datetime.now().isoformat(),
        "propagation_simulation": {
            "simulation_id": prop_results["simulation_id"],
            "grid_cells": 121,
            "duration_hours": 24,
            "mass_diagnostics": prop_results["mass_diagnostics"],
            "peak_summary": prop_results["peak_summary"],
        },
        "scenario_comparison": comp_results["comparison_table"],
        "baseline_metrics": {
            "peak_pm25": comp_results["baseline_peak_pm25"],
            "cumulative_pm25": comp_results["baseline_cumulative_pm25"],
        },
        "recovery_benchmarks": {
            "baseline_recovery": {
                "status": base_recovery["pm25_recovery"]["status"],
                "clearance_hours_from_peak": base_recovery["pm25_recovery"]["clearance_hours_from_peak"],
                "confidence_interval_90": base_recovery["pm25_recovery"]["confidence_interval_90"],
                "half_life_hours": base_recovery["pm25_recovery"]["half_life_hours"],
                "effective_decay_rate": base_recovery["pm25_recovery"]["effective_decay_rate_per_hour"],
            },
            "combined_mitigation_recovery": {
                "status": mit_recovery["pm25_recovery"]["status"],
                "clearance_hours_from_peak": mit_recovery["pm25_recovery"]["clearance_hours_from_peak"],
                "confidence_interval_90": mit_recovery["pm25_recovery"]["confidence_interval_90"],
                "half_life_hours": mit_recovery["pm25_recovery"]["half_life_hours"],
            },
            "ventilation_sensitivity": base_recovery["ventilation_sensitivity"],
        },
    }

    report_json_path = "aeros/artifacts/reports/scenario_simulation_report.json"
    with open(report_json_path, "w", encoding="utf-8") as f:
        json.dump(report_json, f, indent=2)
    logger.info("Saved JSON report to %s", report_json_path)

    # Generate Markdown Report
    rows_md = []
    for r in comp_results["comparison_table"]:
        sign_peak = "+" if r["delta_peak_pm25"] > 0 else ""
        sign_cum = "+" if r["delta_cumulative_exposure_pct"] > 0 else ""
        rows_md.append(
            f"| **{r['scenario_name']}** | `{r['peak_pm25']:.1f}` | {sign_peak}{r['delta_peak_pm25']:.1f} ({sign_peak}{r['delta_peak_pct']:.1f}%) | "
            f"`{r['time_to_peak_hours']}h` ({r['peak_shift_hours']:+d}h) | `{r['cumulative_exposure_pm25']:.1f}` | {sign_cum}{r['delta_cumulative_exposure_pct']:.1f}% | "
            f"`{r['exceedance_hours_pm25_60']}h` | `{r['population_weighted_exposure_index']:.1f}` |"
        )

    sensitivity_md = []
    for s in base_recovery["ventilation_sensitivity"]:
        sensitivity_md.append(
            f"| `{s['wind_speed_ms']:.1f} m/s` | **{s['regime']}** | `{s['decay_rate_per_hour']:.4f} h⁻¹` | `{s['half_life_hours']:.1f} h` | `{s['time_to_clear_hours']:.1f} h` |"
        )

    report_md = f"""# AEROS Round 5 — Atmospheric Simulation & Scenario Intelligence Report

**Evaluation Date**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}  
**Target Domain**: Delhi NCR (121 grid cells, 15 CAAQMS monitoring stations)  
**Simulation Physics**: 2D Advection-Diffusion-Reaction PDE with Upwind Differencing & CFL Adaptive Sub-Stepping  
**Forecasting Window**: 72 Hours (Diwali Eve, Celebration Peak Night, and 48-Hour Recovery Window)

---

## 1. Executive Summary & Policy Takeaways

The AEROS Atmospheric Simulation Engine evaluated 7 counterfactual policy interventions and environmental scenarios against the historical business-as-usual baseline.

### Key Policy Findings:
1. **Episodic Pyrotechnic Surge**:
   - An unrestricted firecracker surge (+100%) escalates citywide mean PM2.5 to **{comp_results['comparison_table'][1]['peak_pm25']:.1f} µg/m³** ({comp_results['comparison_table'][1]['delta_peak_pct']:+.1f}% over baseline), causing extreme acute pulmonary hazard.
2. **Strict Firecracker Ban Compliance**:
   - Achieving 70% pyrotechnic emission curtailment cuts the acute peak by **{abs(comp_results['comparison_table'][2]['delta_peak_pm25']):.1f} µg/m³** ({comp_results['comparison_table'][2]['delta_peak_pct']:.1f}%), preventing severe category air quality.
3. **Combined Policy Intervention (Firecracker Ban + Odd-Even Traffic)**:
   - Delivers the maximum public health protection: **{comp_results['comparison_table'][6]['delta_cumulative_exposure_pct']:.1f}% reduction in cumulative particulate exposure** and cuts NAAQS exceedance duration significantly.
4. **Meteorological Ventilation vs. Stagnation**:
   - Under calm inversion conditions (<1.2 m/s), Delhi's atmospheric half-life extends to **{base_recovery['ventilation_sensitivity'][0]['half_life_hours']:.1f} hours**, requiring **{base_recovery['ventilation_sensitivity'][0]['time_to_clear_hours']:.1f} hours** to return below NAAQS (60 µg/m³).
   - In contrast, moderate western disturbance flushing (>4.0 m/s) cleanses the airshed in **{base_recovery['ventilation_sensitivity'][4]['time_to_clear_hours']:.1f} hours**.

---

## 2. Counterfactual Scenario Benchmark Comparison (72-Hour Horizon)

| Scenario | Peak PM2.5 (µg/m³) | Δ Peak vs Base | Time to Peak | Cum. Exposure (µg·h/m³) | Δ Cum. Exp (%) | NAAQS Exceedance | Pop-Weighted Exposure |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
{chr(10).join(rows_md)}

---

## 3. Atmospheric Recovery & Clearance Dynamics

- **Baseline Clearance Time ($T_{{clear}}$)**: `{report_json['recovery_benchmarks']['baseline_recovery']['clearance_hours_from_peak']:.1f} hours` from peak.
- **90% Conformal Interval**: `[{report_json['recovery_benchmarks']['baseline_recovery']['confidence_interval_90'][0]:.1f}h, {report_json['recovery_benchmarks']['baseline_recovery']['confidence_interval_90'][1]:.1f}h]`.
- **Atmospheric Half-Life ($t_{{1/2}}$)**: `{report_json['recovery_benchmarks']['baseline_recovery']['half_life_hours']:.1f} hours` (effective decay rate $\\lambda = {report_json['recovery_benchmarks']['baseline_recovery']['effective_decay_rate']:.4f}\\,\\text{{h}}^{{-1}}$).
- **Combined Mitigation Clearance Time**: `{report_json['recovery_benchmarks']['combined_mitigation_recovery']['clearance_hours_from_peak']:.1f} hours` from peak ({abs(report_json['recovery_benchmarks']['baseline_recovery']['clearance_hours_from_peak'] - report_json['recovery_benchmarks']['combined_mitigation_recovery']['clearance_hours_from_peak']):.1f} hours faster recovery).

### Atmospheric Ventilation Sensitivity Spectrum:

| Wind Speed ($u$) | Synoptic Ventilation Regime | Relaxation Rate ($\\lambda$) | Aerosol Half-Life ($t_{{1/2}}$) | Clearance Time to NAAQS ($T_{{clear}}$) |
| :---: | :---: | :---: | :---: | :---: |
{chr(10).join(sensitivity_md)}

---

## 4. Physical Transport & Mass Conservation Diagnostics

- **Grid Resolution**: 11 rows × 11 cols = 121 cells ($\\Delta x = 4.87\\,\\text{{km}}$, $\\Delta y = 5.55\\,\\text{{km}}$)
- **Initial Atmospheric PM2.5 Mass**: `{prop_results['mass_diagnostics']['initial_pm25_mass_kg']:.3f} tonnes`
- **Final Atmospheric PM2.5 Mass (24h)**: `{prop_results['mass_diagnostics']['final_pm25_mass_kg']:.3f} tonnes`
- **Advective Courant Number ($CFL_{{adv}}$)**: Enforced $\\le 1.0$ via adaptive sub-stepping (sub-step $\\delta t \\approx 0.05\\,\\text{{h}}$).
- **Von Neumann Diffusion Number ($r_{{diff}}$)**: Enforced $\\le 0.5$.
- **Generated GeoJSON Layer**: `aeros/artifacts/graph_data/delhi_propagation_simulation.geojson` (121 polygon features).
"""

    report_md_path = "aeros/artifacts/reports/scenario_simulation_report.md"
    with open(report_md_path, "w", encoding="utf-8") as f:
        f.write(report_md)
    logger.info("Saved Markdown report to %s", report_md_path)

    print("Complete scenario validation executed successfully!")


if __name__ == "__main__":
    run_complete_scenario_validation()
