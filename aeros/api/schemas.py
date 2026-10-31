"""Pydantic Request and Response Schemas for AEROS API."""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from aeros.simulation.scenarios import ScenarioType


# --- Weather & Propagation Schemas ---

class WeatherConditionInput(BaseModel):
    wind_speed_ms: float = Field(2.5, description="Wind speed in meters per second")
    wind_dir_deg: float = Field(315.0, description="Wind direction azimuth (degrees from North)")
    rainfall_mm: float = Field(0.0, description="Precipitation in millimeters")
    temperature_c: Optional[float] = Field(22.0, description="Ambient air temperature in Celsius")
    humidity_pct: Optional[float] = Field(55.0, description="Relative humidity percentage")


class PropagationSimulationRequest(BaseModel):
    initial_pm25: Optional[Dict[str, float]] = Field(
        default=None,
        description="Mapping of station neighborhood IDs to initial PM2.5 concentrations (µg/m³)"
    )
    initial_pm10: Optional[Dict[str, float]] = Field(
        default=None,
        description="Mapping of station neighborhood IDs to initial PM10 concentrations (µg/m³)"
    )
    weather_sequence: Optional[List[WeatherConditionInput]] = Field(
        default=None,
        description="Hourly sequence of meteorological conditions"
    )
    duration_hours: int = Field(24, ge=1, le=72, description="Simulation duration in hours (1-72)")
    start_time_iso: Optional[str] = Field("2025-10-20T18:00:00", description="Simulation start ISO timestamp")


class PropagationSimulationResponse(BaseModel):
    simulation_id: str
    start_time: str
    duration_hours: int
    timestamps: List[str]
    mass_diagnostics: Dict[str, float]
    peak_summary: Dict[str, Any]
    station_pm25_series: Dict[str, List[float]]
    station_pm10_series: Dict[str, List[float]]
    peak_hour_geojson: Dict[str, Any]
    final_hour_geojson: Dict[str, Any]


# --- Counterfactual Scenario Schemas ---

class ScenarioSimulationRequest(BaseModel):
    scenario_type: ScenarioType = Field(ScenarioType.BASELINE, description="Policy or environmental scenario")
    initial_pm25: Optional[Dict[str, float]] = Field(default=None, description="Initial station PM2.5 (µg/m³)")
    initial_pm10: Optional[Dict[str, float]] = Field(default=None, description="Initial station PM10 (µg/m³)")
    start_time_iso: str = Field("2025-10-19T18:00:00", description="Simulation start ISO timestamp")
    diwali_night_iso: str = Field("2025-10-20T18:00:00", description="Diwali night start ISO timestamp")
    duration_hours: int = Field(72, ge=1, le=72, description="Simulation duration in hours")


class ScenarioSimulationResponse(BaseModel):
    scenario_type: str
    scenario_name: str
    description: str
    start_time: str
    duration_hours: int
    peak_pm25: float
    peak_pm10: float
    max_hotspot_pm25: float
    peak_hour: int
    peak_timestamp: Optional[str]
    cumulative_exposure_pm25: float
    cumulative_exposure_pm10: float
    exceedance_hours_pm25_60: int
    exceedance_hours_pm25_250: int
    exceedance_hours_pm10_100: int
    population_weighted_exposure_index: float
    hourly_mean_pm25_series: List[float]
    hourly_mean_pm10_series: List[float]
    timestamps: List[str]


class ScenarioComparisonRequest(BaseModel):
    scenarios: Optional[List[ScenarioType]] = Field(
        default=None,
        description="List of scenarios to evaluate. If empty, evaluates all 7 supported scenarios."
    )
    initial_pm25: Optional[Dict[str, float]] = None
    initial_pm10: Optional[Dict[str, float]] = None
    duration_hours: int = Field(72, ge=1, le=72)


class ScenarioComparisonItem(BaseModel):
    scenario_type: str
    scenario_name: str
    peak_pm25: float
    delta_peak_pm25: float
    delta_peak_pct: float
    time_to_peak_hours: int
    peak_shift_hours: int
    cumulative_exposure_pm25: float
    delta_cumulative_exposure_pct: float
    exceedance_hours_pm25_60: int
    population_weighted_exposure_index: float


class ScenarioComparisonResponse(BaseModel):
    reference_scenario: str
    duration_hours: int
    baseline_peak_pm25: float
    baseline_cumulative_pm25: float
    comparison_table: List[ScenarioComparisonItem]


# --- Atmospheric Recovery Schemas ---

class RecoveryPredictionRequest(BaseModel):
    pm25_series: List[float] = Field(..., description="Hourly sequence of PM2.5 concentrations (µg/m³)")
    pm10_series: Optional[List[float]] = Field(None, description="Optional sequence of PM10 concentrations (µg/m³)")
    timestamps: Optional[List[str]] = Field(None, description="Optional ISO timestamps")
    target_pm25_threshold: float = Field(60.0, description="Clearance target threshold for PM2.5 (NAAQS: 60.0)")
    target_pm10_threshold: float = Field(100.0, description="Clearance target threshold for PM10 (NAAQS: 100.0)")
    wind_speed_ms: float = Field(2.5, description="Prevailing post-peak wind speed in m/s")
    rainfall_mm: float = Field(0.0, description="Rainfall precipitation in mm")


class RecoveryDetail(BaseModel):
    status: str
    target_threshold: float
    peak_value: float
    peak_hour_from_start: int
    peak_timestamp: Optional[str]
    effective_decay_rate_per_hour: float
    half_life_hours: float
    clearance_hours_from_peak: float
    clearance_hours_from_start: float
    projected_clearance_timestamp: Optional[str]
    recovery_achieved_within_horizon: bool
    confidence_interval_90: List[float]
    recovery_curve_sample: Dict[str, Any]


class VentilationSensitivityItem(BaseModel):
    wind_speed_ms: float
    regime: str
    decay_rate_per_hour: float
    half_life_hours: float
    time_to_clear_hours: float


class RecoveryPredictionResponse(BaseModel):
    pm25_recovery: RecoveryDetail
    pm10_recovery: Optional[RecoveryDetail] = None
    wind_speed_ms: float
    rainfall_mm: float
    ventilation_sensitivity: List[VentilationSensitivityItem]


# --- Spatial Neighborhood Request / Response ---

class NeighborhoodPredictionRequest(BaseModel):
    latitude: float = Field(..., ge=28.25, le=29.00, description="Latitude within Delhi NCR (28.25 - 29.00)")
    longitude: float = Field(..., ge=76.75, le=77.60, description="Longitude within Delhi NCR (76.75 - 77.60)")
    timestamp: Optional[str] = None
    weather_conditions: Optional[Dict[str, float]] = None


class TargetLocationInfo(BaseModel):
    latitude: float
    longitude: float
    confidence_rating: str
    distance_to_nearest_monitor_km: float


class NearestStationInfo(BaseModel):
    station_id: str
    name: str
    classification: str


class PollutantEstimate(BaseModel):
    point_estimate: float
    lower_bound: float
    upper_bound: float
    unit: str


class NeighborhoodPredictionResponse(BaseModel):
    status: str
    prediction_timestamp: str
    target_location: TargetLocationInfo
    nearest_monitoring_station: NearestStationInfo
    pm2_5: PollutantEstimate
    pm10: PollutantEstimate
    model_metadata: Dict[str, Any]
    supporting_stations: Optional[List[Dict[str, Any]]] = None
    model_comparison: Optional[Dict[str, Any]] = None


# --- Air Quality Forecasting Schemas ---

class AirQualityPredictionRequest(BaseModel):
    neighborhood_id: Optional[str] = Field("anand_vihar", description="CAAQMS station neighborhood identifier")
    latitude: Optional[float] = Field(None, ge=28.25, le=29.00)
    longitude: Optional[float] = Field(None, ge=76.75, le=77.60)
    horizon_hours: int = Field(24, ge=1, le=72, description="Forecasting lead horizon (1h to 72h)")
    model_name: Optional[str] = Field("ensemble", description="Model: ensemble, xgboost, transformer, lstm, gru")
    weather_conditions: Optional[Dict[str, float]] = None
    timestamp: Optional[str] = None


class HourlyForecastPoint(BaseModel):
    lead_hour: int
    timestamp: str
    pm25: float
    pm10: float
    aqi: int
    confidence_interval_90_pm25: List[float]


class FeatureImportanceItem(BaseModel):
    feature: str
    importance: float
    impact: str


class AirQualityPredictionResponse(BaseModel):
    status: str
    neighborhood_id: str
    station_name: str
    latitude: float
    longitude: float
    forecast_horizon_hours: int
    model_used: str
    prediction_timestamp: str
    target_timestamp: str
    predicted_pm25: float
    predicted_pm10: float
    predicted_aqi: int
    aqi_category: str
    aqi_color: str
    confidence_interval_90_pm25: List[float]
    confidence_interval_90_pm10: List[float]
    hourly_timeline: List[HourlyForecastPoint]
    feature_importance: List[FeatureImportanceItem]
    model_metadata: Dict[str, Any]


# --- Spatial Intelligence Schemas ---

class SpatialPredictionRequest(BaseModel):
    latitude: float = Field(28.6139, ge=28.25, le=29.00)
    longitude: float = Field(77.2090, ge=76.75, le=77.60)
    neighborhood_id: Optional[str] = None
    timestamp: Optional[str] = None
    weather_conditions: Optional[Dict[str, float]] = None
    model_type: Optional[str] = Field("graphsage", description="GNN architecture or baseline")


# --- Overview & Monitoring Station Schemas ---

class StationDetailItem(BaseModel):
    station_id: str
    neighborhood_id: str
    name: str
    latitude: float
    longitude: float
    classification: str
    road_density_factor: float
    pm2_5: float
    pm10: float
    aqi: int
    aqi_category: str
    aqi_color: str
    last_updated: str


class AlertItem(BaseModel):
    severity: str
    headline: str
    details: str
    timestamp: str


class OverviewResponse(BaseModel):
    status: str
    city: str
    timestamp: str
    citywide_pm25: Dict[str, float]
    citywide_pm10: Dict[str, float]
    citywide_aqi: int
    aqi_category: str
    aqi_color: str
    active_monitors_count: int
    total_grid_cells: int
    weather_summary: Dict[str, Any]
    active_alerts: List[AlertItem]
    stations: List[StationDetailItem]
    system_status: Dict[str, Any]

