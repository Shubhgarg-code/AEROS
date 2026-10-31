/**
 * AEROS Production API Client
 * Connects directly to FastAPI backend service
 * Supports local development (http://localhost:8000) and Vercel production (/api)
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

const isLocalhost =
  typeof window !== 'undefined' &&
  (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1');

// Base URL detection: explicit VITE_API_URL > direct localhost:8000 in dev > relative path in prod
const API_BASE_URL =
  import.meta.env.VITE_API_URL ||
  (isLocalhost && window.location.port !== '8000' ? 'http://localhost:8000' : '');

class AerosApiClient {
  private baseUrl: string;

  constructor(baseUrl: string = API_BASE_URL) {
    this.baseUrl = baseUrl.replace(/\/+$/, '');
  }

  private async request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
    const cleanEndpoint = endpoint.startsWith('/') ? endpoint : `/${endpoint}`;

    // Candidate URLs to try in order of preference
    const candidates: string[] = [];

    if (this.baseUrl) {
      candidates.push(`${this.baseUrl}${cleanEndpoint}`);
      if (!this.baseUrl.endsWith('/api') && !cleanEndpoint.startsWith('/api')) {
        candidates.push(`${this.baseUrl}/api${cleanEndpoint}`);
      }
    }

    // Direct localhost:8000 target for local development
    if (isLocalhost) {
      const localDirect = `http://localhost:8000${cleanEndpoint}`;
      if (!candidates.includes(localDirect)) {
        candidates.push(localDirect);
      }
      const localApi = `http://localhost:8000/api${cleanEndpoint}`;
      if (!candidates.includes(localApi)) {
        candidates.push(localApi);
      }
    }

    // Relative targets (for Vercel rewrites / proxy)
    if (!candidates.includes(cleanEndpoint)) {
      candidates.push(cleanEndpoint);
    }
    const relApi = `/api${cleanEndpoint}`;
    if (!candidates.includes(relApi)) {
      candidates.push(relApi);
    }

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

    let lastError: Error | null = null;

    for (let i = 0; i < candidates.length; i++) {
      const url = candidates[i];
      try {
        const response = await fetch(url, config);

        if (response.ok) {
          return (await response.json()) as T;
        }

        // If 404, try next candidate URL before failing
        if (response.status === 404 && i < candidates.length - 1) {
          continue;
        }

        let errorDetail = `HTTP ${response.status} ${response.statusText}`;
        try {
          const errorJson = await response.json();
          errorDetail = errorJson.detail || errorDetail;
        } catch (_) {
          // ignore parsing error
        }
        throw new Error(errorDetail);
      } catch (err: any) {
        lastError = err;
        // On connection errors, try next candidate URL
        if (i < candidates.length - 1) {
          continue;
        }
      }
    }

    console.error(`AEROS API Error at ${endpoint}:`, lastError);
    throw lastError || new Error(`Unable to connect to ${endpoint}`);
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
