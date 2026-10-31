/**
 * TypeScript Data Models matching AEROS Backend API Schemas
 */

export interface StationDetail {
  station_id: string;
  neighborhood_id: string;
  name: string;
  latitude: number;
  longitude: number;
  classification: string;
  road_density_factor: number;
  pm2_5?: number;
  pm10?: number;
  current_pm25?: number;
  current_pm10?: number;
  aqi: number;
  aqi_category: string;
  aqi_color: string;
  last_updated?: string;
  is_holdout?: boolean;
}

export interface AlertItem {
  severity: 'INFO' | 'WARNING' | 'CRITICAL';
  headline: string;
  details: string;
  timestamp: string;
}

export interface OverviewData {
  status: string;
  city: string;
  timestamp: string;
  citywide_pm25: {
    mean: number;
    max: number;
    min: number;
  };
  citywide_pm10: {
    mean: number;
    max: number;
    min: number;
  };
  citywide_aqi: number;
  aqi_category: string;
  aqi_color: string;
  active_monitors_count: number;
  total_grid_cells: number;
  weather_summary: {
    wind_speed_ms: number;
    wind_direction_deg: number;
    wind_direction_compass: string;
    temperature_c: number;
    humidity_pct: number;
    pbl_height_m: number;
    inversion_risk: string;
  };
  active_alerts: AlertItem[];
  stations: StationDetail[];
  system_status: {
    pipeline_status: string;
    last_model_retrain: string;
    prediction_engine: string;
    data_source: string;
  };
}

export interface HourlyForecastPoint {
  lead_hour: number;
  timestamp: string;
  pm25: number;
  pm10: number;
  aqi: number;
  confidence_interval_90_pm25: [number, number];
}

export interface FeatureImportanceItem {
  feature: string;
  importance: number;
  impact: string;
}

export interface AirQualityForecastData {
  status: string;
  neighborhood_id: string;
  station_name: string;
  latitude: number;
  longitude: number;
  forecast_horizon_hours: number;
  model_used: string;
  prediction_timestamp: string;
  target_timestamp: string;
  predicted_pm25: number;
  predicted_pm10: number;
  predicted_aqi: number;
  aqi_category: string;
  aqi_color: string;
  confidence_interval_90_pm25: [number, number];
  confidence_interval_90_pm10: [number, number];
  hourly_timeline: HourlyForecastPoint[];
  feature_importance: FeatureImportanceItem[];
  model_metadata: {
    algorithm: string;
    test_pm25_mae: number;
    calibration_method: string;
  };
}

export interface SupportingStation {
  station_id: string;
  name: string;
  neighborhood_id: string;
  distance_km: number;
  weight: number;
  pm2_5: number;
  pm10: number;
}

export interface SpatialPredictionData {
  status: string;
  prediction_timestamp: string;
  target_location: {
    latitude: number;
    longitude: number;
    confidence_rating: 'HIGH' | 'MODERATE' | 'LOW';
    distance_to_nearest_monitor_km: number;
  };
  nearest_monitoring_station: {
    station_id: string;
    name: string;
    classification: string;
  };
  supporting_stations?: SupportingStation[];
  model_comparison?: {
    graphsage_gnn: { pm2_5: number; pm10: number; mae: number; type: string };
    idw_interpolation: { pm2_5: number; pm10: number; mae: number; type: string };
    spatial_xgboost: { pm2_5: number; pm10: number; mae: number; type: string };
  };
  pm2_5: {
    point_estimate: number;
    lower_bound: number;
    upper_bound: number;
    unit: string;
  };
  pm10: {
    point_estimate: number;
    lower_bound: number;
    upper_bound: number;
    unit: string;
  };
  model_metadata: {
    model_version: string;
    methodology: string;
  };
}

export interface PropagationSnapshot {
  step_hour: number;
  timestamp: string;
  mean_pm25: number;
  max_pm25: number;
  mean_pm10: number;
  max_pm10: number;
  wind_speed_ms: number;
  wind_dir_deg: number;
  grid_pm25_snapshot: number[][];
  grid_pm10_snapshot: number[][];
}

export interface PropagationSimulationData {
  simulation_id: string;
  start_time: string;
  duration_hours: number;
  timestamps: string[];
  mass_diagnostics: {
    initial_pm25_mass_kg: number;
    final_pm25_mass_kg: number;
    initial_pm10_mass_kg: number;
    final_pm10_mass_kg: number;
  };
  peak_summary: {
    peak_hour: number;
    peak_timestamp: string;
    max_pm25: number;
    mean_pm25: number;
  };
  hourly_snapshots: PropagationSnapshot[];
  station_pm25_series: Record<string, number[]>;
  station_pm10_series: Record<string, number[]>;
  peak_hour_geojson?: any;
  final_hour_geojson?: any;
}

export type ScenarioType =
  | 'baseline'
  | 'firecracker_increase'
  | 'firecracker_reduction'
  | 'traffic_increase'
  | 'traffic_reduction'
  | 'weather_flushing'
  | 'combined_mitigation';

export interface ScenarioSimulationData {
  scenario_type: string;
  scenario_name: string;
  description: string;
  start_time: string;
  duration_hours: number;
  peak_pm25: number;
  peak_pm10: number;
  max_hotspot_pm25: number;
  peak_hour: number;
  peak_timestamp: string;
  cumulative_exposure_pm25: number;
  cumulative_exposure_pm10: number;
  exceedance_hours_pm25_60: number;
  exceedance_hours_pm25_250: number;
  exceedance_hours_pm10_100: number;
  population_weighted_exposure_index: number;
  hourly_mean_pm25_series: number[];
  hourly_mean_pm10_series: number[];
  timestamps: string[];
}

export interface ScenarioComparisonItem {
  scenario_type: string;
  scenario_name: string;
  peak_pm25: number;
  delta_peak_pm25: number;
  delta_peak_pct: number;
  time_to_peak_hours: number;
  peak_shift_hours: number;
  cumulative_exposure_pm25: number;
  delta_cumulative_exposure_pct: number;
  exceedance_hours_pm25_60: number;
  population_weighted_exposure_index: number;
}

export interface ScenarioComparisonData {
  reference_scenario: string;
  duration_hours: number;
  baseline_peak_pm25: number;
  baseline_cumulative_pm25: number;
  comparison_table: ScenarioComparisonItem[];
}

export interface RecoveryDetail {
  status: string;
  target_threshold: number;
  peak_value: number;
  peak_hour_from_start: number;
  peak_timestamp?: string;
  effective_decay_rate_per_hour: number;
  half_life_hours: number;
  clearance_hours_from_peak: number;
  clearance_hours_from_start: number;
  projected_clearance_timestamp?: string;
  recovery_achieved_within_horizon: boolean;
  confidence_interval_90: [number, number];
  recovery_curve_sample: {
    hours_post_peak: number[];
    projected_concentrations: number[];
  };
}

export interface VentilationSensitivityItem {
  wind_speed_ms: number;
  regime: string;
  decay_rate_per_hour: number;
  half_life_hours: number;
  time_to_clear_hours: number;
}

export interface RecoveryData {
  pm25_recovery: RecoveryDetail;
  pm10_recovery?: RecoveryDetail;
  wind_speed_ms: number;
  rainfall_mm: number;
  ventilation_sensitivity: VentilationSensitivityItem[];
}

export interface ModelMetadata {
  status: string;
  system_name: string;
  version: string;
  supported_horizons: number[];
  temporal_models: Array<{
    model: string;
    pm25_mae: number;
    pm25_rmse: number;
    pm25_r2: number;
    pm10_mae: number;
  }>;
  spatial_models: Array<{
    model: string;
    pm25_mae: number;
    pm25_rmse: number;
    pm25_r2: number;
  }>;
  scenario_benchmarks: ScenarioComparisonItem[];
  spatial_grid_specs: {
    rows: number;
    cols: number;
    total_cells: number;
    resolution_degrees: number;
    resolution_km: string;
    bounds: { lat_min: number; lat_max: number; lon_min: number; lon_max: number };
  };
  known_limitations: string[];
}

export interface HealthData {
  status: string;
  system: string;
  spatial_grid: {
    rows: number;
    cols: number;
    total_cells: number;
    resolution_deg: number;
    domain: string;
  };
  monitored_stations_count: number;
  supported_scenarios: string[];
  physics_solver: {
    advection_scheme: string;
    diffusion_scheme: string;
    time_integration: string;
    cfl_stability_enforced: boolean;
    mass_conservation_checked: boolean;
  };
  recovery_model: {
    decay_formulation: string;
    conformal_calibration_level: number;
    standard_naaqs_pm25: number;
    standard_naaqs_pm10: number;
  };
}
