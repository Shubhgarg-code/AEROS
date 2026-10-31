"""Diwali What-If Scenario Definitions and Emission Profiles for AEROS.

Defines scientifically defensible emission perturbations, diurnal profiles,
and meteorological modifiers for counterfactual atmospheric modeling.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional
import numpy as np


class ScenarioType(str, Enum):
    """Supported counterfactual intervention and meteorological scenarios."""
    BASELINE = "baseline"
    FIRECRACKER_INCREASE = "firecracker_increase"
    FIRECRACKER_REDUCTION = "firecracker_reduction"
    TRAFFIC_INCREASE = "traffic_increase"
    TRAFFIC_REDUCTION = "traffic_reduction"
    WEATHER_FLUSHING = "weather_flushing"
    COMBINED_MITIGATION = "combined_mitigation"


@dataclass
class ScenarioConfig:
    """Configuration parameters for a counterfactual scenario."""
    scenario_type: ScenarioType
    name: str
    description: str
    firecracker_multiplier: float  # Scale on episodic firecracker emission pulse
    traffic_multiplier: float      # Scale on diurnal vehicular traffic emissions
    wind_speed_delta_ms: float     # Additive shift to wind speed (m/s)
    rainfall_delta_mm: float       # Additive rainfall (mm)
    pblh_multiplier: float         # Planetary boundary layer height multiplier


SCENARIO_REGISTRY: Dict[ScenarioType, ScenarioConfig] = {
    ScenarioType.BASELINE: ScenarioConfig(
        scenario_type=ScenarioType.BASELINE,
        name="Baseline (Business As Usual)",
        description="Standard historical Diwali conditions with typical firecracker activity and normal holiday traffic.",
        firecracker_multiplier=1.0,
        traffic_multiplier=1.0,
        wind_speed_delta_ms=0.0,
        rainfall_delta_mm=0.0,
        pblh_multiplier=1.0,
    ),
    ScenarioType.FIRECRACKER_INCREASE: ScenarioConfig(
        scenario_type=ScenarioType.FIRECRACKER_INCREASE,
        name="Severe Firecracker Surge (+100%)",
        description="Unrestricted pyrotechnic emissions representing a 100% surge in episodic bursting volume.",
        firecracker_multiplier=2.0,
        traffic_multiplier=1.0,
        wind_speed_delta_ms=0.0,
        rainfall_delta_mm=0.0,
        pblh_multiplier=1.0,
    ),
    ScenarioType.FIRECRACKER_REDUCTION: ScenarioConfig(
        scenario_type=ScenarioType.FIRECRACKER_REDUCTION,
        name="Strict Firecracker Ban Compliance (-70%)",
        description="Enforced ban on non-green firecrackers achieving 70% pyrotechnic emission reduction.",
        firecracker_multiplier=0.3,
        traffic_multiplier=1.0,
        wind_speed_delta_ms=0.0,
        rainfall_delta_mm=0.0,
        pblh_multiplier=1.0,
    ),
    ScenarioType.TRAFFIC_INCREASE: ScenarioConfig(
        scenario_type=ScenarioType.TRAFFIC_INCREASE,
        name="Festive Traffic Congestion (+30%)",
        description="Post-Diwali commercial and passenger traffic congestion increasing vehicular exhaust by 30%.",
        firecracker_multiplier=1.0,
        traffic_multiplier=1.3,
        wind_speed_delta_ms=0.0,
        rainfall_delta_mm=0.0,
        pblh_multiplier=1.0,
    ),
    ScenarioType.TRAFFIC_REDUCTION: ScenarioConfig(
        scenario_type=ScenarioType.TRAFFIC_REDUCTION,
        name="Odd-Even Vehicle Rationing (-40%)",
        description="Aggressive traffic curtailment via odd-even license rationing and entry bans on heavy diesel vehicles.",
        firecracker_multiplier=1.0,
        traffic_multiplier=0.6,
        wind_speed_delta_ms=0.0,
        rainfall_delta_mm=0.0,
        pblh_multiplier=1.0,
    ),
    ScenarioType.WEATHER_FLUSHING: ScenarioConfig(
        scenario_type=ScenarioType.WEATHER_FLUSHING,
        name="Atmospheric Ventilation & Flushing",
        description="Strong synoptic post-frontal western disturbance increasing surface winds (+3.5 m/s) and deepening mixing layer.",
        firecracker_multiplier=1.0,
        traffic_multiplier=1.0,
        wind_speed_delta_ms=3.5,
        rainfall_delta_mm=0.5,
        pblh_multiplier=1.4,
    ),
    ScenarioType.COMBINED_MITIGATION: ScenarioConfig(
        scenario_type=ScenarioType.COMBINED_MITIGATION,
        name="Combined Policy Mitigation (Ban + Traffic Curb)",
        description="Comprehensive emergency action combining strict firecracker ban (-70%) and Odd-Even vehicle rationing (-40%).",
        firecracker_multiplier=0.3,
        traffic_multiplier=0.6,
        wind_speed_delta_ms=0.0,
        rainfall_delta_mm=0.0,
        pblh_multiplier=1.0,
    ),
}


def compute_diurnal_traffic_profile(hour_of_day: float) -> float:
    """Computes normalized diurnal vehicular traffic emission factor [0.2, 1.8].
    
    Bimodal distribution peaking at morning rush (8:00-10:00) and evening rush (17:00-20:00).
    """
    # Morning peak centered at 9.0 (sigma 1.8)
    morning_peak = 1.4 * np.exp(-((hour_of_day - 9.0) ** 2) / (2.0 * (1.8 ** 2)))
    # Evening peak centered at 18.5 (sigma 2.2)
    evening_peak = 1.6 * np.exp(-((hour_of_day - 18.5) ** 2) / (2.0 * (2.2 ** 2)))
    # Nighttime baseline minimum
    base_activity = 0.25
    return float(base_activity + morning_peak + evening_peak)


def compute_firecracker_emission_pulse(
    rel_hour_from_diwali_night: float,
    base_amplitude_pm25: float = 65.0,  # µg/m³/h peak rate
) -> Tuple[float, float]:
    """Computes episodic pyrotechnic emission pulse for PM2.5 and PM10.
    
    rel_hour_from_diwali_night: 0.0 corresponds to 18:00 on Diwali night.
    Peak occurs at rel_hour = 3.5 (approx 21:30 PM), decaying rapidly by rel_hour = 8.0 (02:00 AM).
    
    Firecracker emissions are highly dominated by fine particulate matter:
        PM2.5 fraction ≈ 0.72, PM10 fraction ≈ 1.0 (PM10 = PM2.5 / 0.72)
    
    Returns:
        (s_pm25, s_pm10) emission rate in µg/m³/h
    """
    if rel_hour_from_diwali_night < -2.0 or rel_hour_from_diwali_night > 12.0:
        return 0.0, 0.0

    # Skewed pulse centered around 3.5 hours into celebration
    t = rel_hour_from_diwali_night
    sigma = 2.0 if t <= 3.5 else 2.8
    pulse = float(np.exp(-((t - 3.5) ** 2) / (2.0 * (sigma ** 2))))

    s_pm25 = float(base_amplitude_pm25 * pulse)
    s_pm10 = float(s_pm25 / 0.72)  # High fine-particle ratio
    return s_pm25, s_pm10
