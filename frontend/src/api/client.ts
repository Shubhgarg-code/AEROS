/**
 * AEROS Production API Client
 * Connects directly to FastAPI backend service at VITE_API_URL
 */

import {
  AirQualityForecastData,
  HealthData,
  ModelMetadata,
  OverviewData,
  PropagationSimulationData,
  RecoveryData,
  ScenarioComparisonData,
  ScenarioSimulationData,
  SpatialPredictionData,
  StationDetail,
} from '../types';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

class AerosApiClient {
  private baseUrl: string;

  constructor(baseUrl: string = API_BASE_URL) {
    this.baseUrl = baseUrl.replace(/\/+$/, '');
  }

  private async request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
    const url = `${this.baseUrl}${endpoint.startsWith('/') ? endpoint : `/${endpoint}`}`;
    const defaultHeaders = {
      'Content-Type': 'application/json',
      Accept: 'application/json',
    };

    const config: RequestInit = {
      ...options,
      headers: {
        ...defaultHeaders,
        ...options.headers,
      },
    };

    try {
      const response = await fetch(url, config);

      if (!response.ok) {
        let errorDetail = `HTTP ${response.status} ${response.statusText}`;
        try {
          const errorJson = await response.json();
          errorDetail = errorJson.detail || errorDetail;
        } catch (_) {
          // ignore parsing error
        }
        throw new Error(errorDetail);
      }

      return (await response.json()) as T;
    } catch (error: any) {
      console.error(`AEROS API Error at ${endpoint}:`, error);
      throw error;
    }
  }

  // --- 1. Overview Dashboard ---
  async getOverview(): Promise<OverviewData> {
    return this.request<OverviewData>('/overview');
  }

  // --- 2. Monitoring Stations ---
  async getStations(): Promise<{ status: string; count: number; stations: StationDetail[] }> {
    return this.request<{ status: string; count: number; stations: StationDetail[] }>('/stations');
  }

  // --- 3. GeoJSON Layers ---
  async getHeatmapGeoJSON(): Promise<any> {
    return this.request<any>('/geojson/heatmap');
  }

  async getGridGeoJSON(): Promise<any> {
    return this.request<any>('/geojson/grid');
  }

  // --- 4. Air Quality Forecasting ---
  async predictAirQuality(params: {
    neighborhood_id?: string;
    latitude?: number;
    longitude?: number;
    horizon_hours?: number;
    model_name?: string;
    weather_conditions?: Record<string, number>;
  }): Promise<AirQualityForecastData> {
    return this.request<AirQualityForecastData>('/predict/air-quality', {
      method: 'POST',
      body: JSON.stringify(params),
    });
  }

  // --- 5. Spatial Intelligence ---
  async predictSpatial(params: {
    latitude: number;
    longitude: number;
    neighborhood_id?: string;
    weather_conditions?: Record<string, number>;
    model_type?: string;
  }): Promise<SpatialPredictionData> {
    return this.request<SpatialPredictionData>('/predict/spatial', {
      method: 'POST',
      body: JSON.stringify(params),
    });
  }

  // --- 6. Pollution Propagation Simulation ---
  async simulatePropagation(params: {
    duration_hours?: number;
    initial_pm25?: Record<string, number>;
    initial_pm10?: Record<string, number>;
    weather_sequence?: Array<{ wind_speed_ms: number; wind_dir_deg: number; rainfall_mm: number }>;
  }): Promise<PropagationSimulationData> {
    return this.request<PropagationSimulationData>('/simulate/propagation', {
      method: 'POST',
      body: JSON.stringify(params),
    });
  }

  // --- 7. Diwali What-If Scenario Simulator ---
  async simulateScenario(params: {
    scenario_type: string;
    duration_hours?: number;
    initial_pm25?: Record<string, number>;
    initial_pm10?: Record<string, number>;
    start_time_iso?: string;
    diwali_night_iso?: string;
  }): Promise<ScenarioSimulationData> {
    return this.request<ScenarioSimulationData>('/simulate/scenario', {
      method: 'POST',
      body: JSON.stringify(params),
    });
  }

  // --- 8. Scenario Comparison Matrix ---
  async compareScenarios(params: {
    scenarios?: string[];
    duration_hours?: number;
    initial_pm25?: Record<string, number>;
    initial_pm10?: Record<string, number>;
  }): Promise<ScenarioComparisonData> {
    return this.request<ScenarioComparisonData>('/compare/scenarios', {
      method: 'POST',
      body: JSON.stringify(params),
    });
  }

  // --- 9. Atmospheric Recovery Predictor ---
  async predictRecovery(params: {
    pm25_series: number[];
    pm10_series?: number[];
    timestamps?: string[];
    target_pm25_threshold?: number;
    target_pm10_threshold?: number;
    wind_speed_ms?: number;
    rainfall_mm?: number;
  }): Promise<RecoveryData> {
    return this.request<RecoveryData>('/predict/recovery', {
      method: 'POST',
      body: JSON.stringify(params),
    });
  }

  // --- 10. System Health & Transparency ---
  async getSimulationHealth(): Promise<HealthData> {
    return this.request<HealthData>('/simulation/health');
  }

  async getModelsMetadata(): Promise<ModelMetadata> {
    return this.request<ModelMetadata>('/models/metadata');
  }
}

export const apiClient = new AerosApiClient();
