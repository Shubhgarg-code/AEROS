"""Atmospheric Recovery Prediction Engine for AEROS.

Predicts clearance trajectories, post-Diwali episodic pollution decay rates,
time-to-clear thresholds, and conformal uncertainty intervals for PM2.5 and PM10.
"""

from datetime import datetime, timedelta
import logging
from typing import Any, Dict, List, Optional, Tuple
import numpy as np

logger = logging.getLogger("aeros.simulation.recovery")

# Statutory Air Quality Standard Thresholds (µg/m³)
DEFAULT_THRESHOLDS = {
    "pm25_naaqs": 60.0,    # Indian 24-hr NAAQS for PM2.5
    "pm10_naaqs": 100.0,   # Indian 24-hr NAAQS for PM10
    "pm25_who": 15.0,      # WHO 24-hr Air Quality Guideline for PM2.5
    "pm10_who": 45.0,      # WHO 24-hr Air Quality Guideline for PM10
    "pm25_moderate": 90.0, # CPCB Moderate breakpoint
    "pm10_moderate": 150.0,# CPCB Moderate breakpoint
}


class AtmosphericRecoveryEngine:
    """Predicts post-peak pollution relaxation, clearance hours, and meteorological sensitivity."""

    def __init__(
        self,
        base_lambda: float = 0.022,  # 1/h baseline dry deposition and natural ventilation
        alpha_wind: float = 0.018,   # 1/h per m/s above stagnant threshold
        alpha_rain: float = 0.065,   # 1/h per mm rainfall scavenging
        alpha_pbl: float = 0.010,    # 1/h per 1000m planetary boundary layer height
        stagnant_wind_threshold: float = 1.2, # m/s
    ):
        self.base_lambda = base_lambda
        self.alpha_wind = alpha_wind
        self.alpha_rain = alpha_rain
        self.alpha_pbl = alpha_pbl
        self.stagnant_wind = stagnant_wind_threshold
        # Residual variance for conformal recovery time prediction (calibrated on historical Diwali data)
        self.sigma_hours = 3.8

    def compute_decay_rate(
        self,
        wind_speed_ms: float = 2.5,
        rainfall_mm: float = 0.0,
        pblh_m: float = 650.0,
    ) -> float:
        """Calculates effective exponential relaxation rate λ (1/h)."""
        eff_wind = max(0.0, wind_speed_ms - self.stagnant_wind)
        lambda_eff = (
            self.base_lambda
            + self.alpha_wind * eff_wind
            + self.alpha_rain * max(0.0, rainfall_mm)
            + self.alpha_pbl * (pblh_m / 1000.0)
        )
        return float(max(0.005, lambda_eff))

    def detect_peak(
        self,
        concentrations: List[float],
        timestamps: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """Identifies peak concentration, index, and timestamp."""
        arr = np.array(concentrations, dtype=np.float32)
        peak_idx = int(np.argmax(arr))
        peak_val = float(arr[peak_idx])

        peak_ts = timestamps[peak_idx] if (timestamps and peak_idx < len(timestamps)) else None

        return {
            "peak_index": peak_idx,
            "peak_value": float(round(peak_val, 2)),
            "peak_timestamp": peak_ts,
        }

    def predict_clearance(
        self,
        time_series: List[float],
        target_threshold: float = 60.0,
        timestamps: Optional[List[str]] = None,
        wind_speed_ms: float = 2.5,
        rainfall_mm: float = 0.0,
        background_concentration: float = 40.0,
    ) -> Dict[str, Any]:
        """Calculates recovery clearance time below statutory or baseline threshold.
        
        Args:
            time_series: Hourly concentration series across simulation or forecast horizon.
            target_threshold: Target concentration threshold (e.g. 60.0 for PM2.5).
            timestamps: Optional list of ISO timestamp strings.
            wind_speed_ms: Prevailing wind speed.
            rainfall_mm: Precipitation.
            background_concentration: Regional background concentration lower bound.
            
        Returns:
            Dictionary with clearance status, hours to clear, confidence bounds, and projected trajectory.
        """
        peak_info = self.detect_peak(time_series, timestamps)
        peak_idx = peak_info["peak_index"]
        peak_val = peak_info["peak_value"]
        total_steps = len(time_series)

        # Check if peak already meets or is below threshold
        if peak_val <= target_threshold:
            return {
                "status": "ALREADY_BELOW_THRESHOLD",
                "peak_value": peak_val,
                "target_threshold": target_threshold,
                "clearance_hours_from_peak": 0.0,
                "clearance_hours_from_start": float(peak_idx),
                "clearance_timestamp": peak_info["peak_timestamp"],
                "confidence_interval_90": [0.0, 0.0],
                "recovery_achieved_within_horizon": True,
            }

        # Scan for first crossing below target_threshold AFTER peak
        crossing_idx = None
        for i in range(peak_idx + 1, total_steps):
            if time_series[i] <= target_threshold:
                crossing_idx = i
                break

        lambda_eff = self.compute_decay_rate(wind_speed_ms=wind_speed_ms, rainfall_mm=rainfall_mm)

        if crossing_idx is not None:
            # Empirical crossing detected within horizon
            hours_from_peak = float(crossing_idx - peak_idx)
            hours_from_start = float(crossing_idx)
            clearance_ts = timestamps[crossing_idx] if (timestamps and crossing_idx < len(timestamps)) else None
            status = "THRESHOLD_REACHED"
            achieved = True

            # 90% conformal interval (z = 1.645)
            ci_lower = max(0.0, round(hours_from_peak - 1.645 * self.sigma_hours, 1))
            ci_upper = round(hours_from_peak + 1.645 * self.sigma_hours, 1)
        else:
            # Threshold not reached within the simulated horizon
            status = "THRESHOLD_NOT_REACHED_WITHIN_HORIZON"
            achieved = False
            clearance_ts = None

            # Project analytical exponential decay from peak:
            # C(t) = C_bg + (C_peak - C_bg) * exp(-lambda * t)
            # t = (1 / lambda) * ln((C_peak - C_bg) / (C_threshold - C_bg))
            bg = min(background_concentration, target_threshold * 0.75)
            if peak_val > bg and target_threshold > bg:
                projected_hours = (1.0 / lambda_eff) * np.log((peak_val - bg) / (target_threshold - bg))
            else:
                projected_hours = float((peak_val - target_threshold) / (lambda_eff * 50.0))

            hours_from_peak = float(round(projected_hours, 1))
            hours_from_start = float(round(peak_idx + projected_hours, 1))

            if timestamps and len(timestamps) > peak_idx:
                try:
                    t_peak_dt = datetime.fromisoformat(timestamps[peak_idx])
                    clearance_ts = (t_peak_dt + timedelta(hours=projected_hours)).isoformat()
                except Exception:
                    clearance_ts = None

            ci_lower = max(0.0, round(hours_from_peak - 1.645 * (self.sigma_hours * 1.5), 1))
            ci_upper = round(hours_from_peak + 1.645 * (self.sigma_hours * 1.5), 1)

        # Generate analytical recovery curve for visualization (from peak up to peak + 96 hours)
        curve_hours = np.arange(0, max(48, int(np.ceil(hours_from_peak * 1.3))), 1)
        bg = min(background_concentration, target_threshold * 0.75)
        curve_vals = [
            float(round(bg + (peak_val - bg) * np.exp(-lambda_eff * h), 2))
            for h in curve_hours
        ]

        return {
            "status": status,
            "target_threshold": target_threshold,
            "peak_value": peak_val,
            "peak_hour_from_start": peak_idx,
            "peak_timestamp": peak_info["peak_timestamp"],
            "effective_decay_rate_per_hour": round(lambda_eff, 4),
            "half_life_hours": round(np.log(2.0) / lambda_eff, 1),
            "clearance_hours_from_peak": hours_from_peak,
            "clearance_hours_from_start": hours_from_start,
            "projected_clearance_timestamp": clearance_ts,
            "recovery_achieved_within_horizon": achieved,
            "confidence_interval_90": [ci_lower, ci_upper],
            "recovery_curve_sample": {
                "hours_post_peak": curve_hours[:36].tolist(),
                "projected_concentrations": curve_vals[:36],
            },
        }

    def evaluate_wind_sensitivity(
        self,
        peak_concentration: float = 450.0,
        target_threshold: float = 60.0,
        wind_speeds: Optional[List[float]] = None,
        background_concentration: float = 40.0,
    ) -> List[Dict[str, Any]]:
        """Evaluates clearance time sensitivity across a spectrum of atmospheric ventilation speeds."""
        if wind_speeds is None:
            wind_speeds = [0.8, 1.5, 2.5, 3.5, 5.0, 7.0]

        sensitivity_table = []
        bg = min(background_concentration, target_threshold * 0.75)

        for ws in wind_speeds:
            lam = self.compute_decay_rate(wind_speed_ms=ws)
            if peak_concentration > bg and target_threshold > bg:
                hours = (1.0 / lam) * np.log((peak_concentration - bg) / (target_threshold - bg))
            else:
                hours = 12.0

            half_life = np.log(2.0) / lam

            if ws < 1.2:
                regime = "Severe Inversion & Stagnation"
            elif ws < 2.5:
                regime = "Calm Winter Dispersion"
            elif ws < 4.5:
                regime = "Moderate Advective Ventilation"
            else:
                regime = "Rapid Synoptic Flushing"

            sensitivity_table.append({
                "wind_speed_ms": ws,
                "regime": regime,
                "decay_rate_per_hour": round(lam, 4),
                "half_life_hours": round(half_life, 1),
                "time_to_clear_hours": round(hours, 1),
            })

        return sensitivity_table
