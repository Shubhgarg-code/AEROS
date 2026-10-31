"""Inference wrapper for Atmospheric Recovery Prediction in AEROS."""

from typing import Any, Dict, List, Optional
from aeros.simulation.recovery import AtmosphericRecoveryEngine, DEFAULT_THRESHOLDS


class AerosRecoveryPredictor:
    """Production serving interface for post-event air quality recovery estimation."""

    def __init__(self):
        self.engine = AtmosphericRecoveryEngine()

    def predict_recovery(
        self,
        pm25_series: List[float],
        pm10_series: Optional[List[float]] = None,
        timestamps: Optional[List[str]] = None,
        target_pm25_threshold: float = DEFAULT_THRESHOLDS["pm25_naaqs"],
        target_pm10_threshold: float = DEFAULT_THRESHOLDS["pm10_naaqs"],
        wind_speed_ms: float = 2.5,
        rainfall_mm: float = 0.0,
    ) -> Dict[str, Any]:
        """Predicts recovery times for PM2.5 and PM10, alongside wind ventilation sensitivity."""
        rec_pm25 = self.engine.predict_clearance(
            time_series=pm25_series,
            target_threshold=target_pm25_threshold,
            timestamps=timestamps,
            wind_speed_ms=wind_speed_ms,
            rainfall_mm=rainfall_mm,
        )

        result: Dict[str, Any] = {
            "pm25_recovery": rec_pm25,
            "wind_speed_ms": wind_speed_ms,
            "rainfall_mm": rainfall_mm,
        }

        if pm10_series is not None and len(pm10_series) > 0:
            rec_pm10 = self.engine.predict_clearance(
                time_series=pm10_series,
                target_threshold=target_pm10_threshold,
                timestamps=timestamps,
                wind_speed_ms=wind_speed_ms,
                rainfall_mm=rainfall_mm,
            )
            result["pm10_recovery"] = rec_pm10

        # Include meteorological ventilation sensitivity table based on peak PM2.5
        peak_pm25 = rec_pm25["peak_value"]
        result["ventilation_sensitivity"] = self.engine.evaluate_wind_sensitivity(
            peak_concentration=peak_pm25,
            target_threshold=target_pm25_threshold,
        )

        return result
