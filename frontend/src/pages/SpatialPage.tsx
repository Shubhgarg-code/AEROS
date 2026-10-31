import React, { useState } from 'react';
import {
  Share2,
  MapPin,
  Compass,
  Layers,
  ArrowRight,
  ShieldCheck,
  AlertCircle,
  HelpCircle,
  Activity,
  Info,
} from 'lucide-react';
import { apiClient } from '../api/client';
import { SpatialPredictionData, SupportingStation } from '../types';
import { MetricCard } from '../components/MetricCard';
import { DisclaimerBanner } from '../components/DisclaimerBanner';

export const SpatialPage: React.FC = () => {
  const [lat, setLat] = useState<number>(28.6139);
  const [lon, setLon] = useState<number>(77.2090);
  const [modelType, setModelType] = useState<string>('graphsage');
  const [windSpeed, setWindSpeed] = useState<number>(2.5);

  const [prediction, setPrediction] = useState<SpatialPredictionData | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  // Preset landmarks across Delhi NCR
  const presetLocations = [
    { name: 'India Gate (Central Delhi)', lat: 28.6129, lon: 77.2295 },
    { name: 'Connaught Place (Commercial)', lat: 28.6315, lon: 77.2167 },
    { name: 'Rohini Sector 16 (Northwest)', lat: 28.7325, lon: 77.1189 },
    { name: 'Saket District Centre (South)', lat: 28.5245, lon: 77.2162 },
    { name: 'Mayur Vihar Phase 1 (East)', lat: 28.6085, lon: 77.2952 },
    { name: 'Dwarka Sector 21 (Southwest)', lat: 28.5522, lon: 77.0588 },
  ];

  const handlePredict = async (targetLat = lat, targetLon = lon) => {
    try {
      setLoading(true);
      setError(null);
      const res = await apiClient.predictSpatial({
        latitude: targetLat,
        longitude: targetLon,
        model_type: modelType,
        weather_conditions: { wind_speed: windSpeed },
      });
      setPrediction(res);
    } catch (err: any) {
      setError(err.message || 'Spatial prediction failed.');
    } finally {
      setLoading(false);
    }
  };

  const handleSelectPreset = (presetLat: number, presetLon: number) => {
    setLat(presetLat);
    setLon(presetLon);
    handlePredict(presetLat, presetLon);
  };

  return (
    <div className="space-y-6">
      <DisclaimerBanner type="observation" />

      {/* Coordinate Input & Presets */}
      <div className="rounded-xl border border-[#E5E5DF] bg-white p-6 shadow-[0_1px_3px_rgba(0,0,0,0.02)]">
        <div className="border-b border-[#F2F2EC] pb-4">
          <h3 className="text-sm font-semibold tracking-tight text-charcoal">
            Neighbourhood Pollution Estimates
          </h3>
          <p className="text-xs text-charcoal-muted">
            Estimate particulate concentrations at unmonitored locations using graph spatial modeling and distance weighting
          </p>
        </div>

        {/* Quick Presets */}
        <div className="mt-4">
          <span className="text-xs font-medium text-charcoal-muted block mb-2">
            Select a representative neighbourhood or landmark:
          </span>
          <div className="flex flex-wrap gap-2">
            {presetLocations.map((p, idx) => (
              <button
                key={idx}
                onClick={() => handleSelectPreset(p.lat, p.lon)}
                className={`rounded-md border px-3 py-1.5 text-xs transition-colors ${
                  Math.abs(lat - p.lat) < 0.001 && Math.abs(lon - p.lon) < 0.001
                    ? 'border-[#CDE5DF] bg-[#EAF4F1] text-[#285D52] font-semibold'
                    : 'border-[#E5E5DF] bg-[#FAFAF7] text-charcoal-muted hover:bg-white hover:text-charcoal'
                }`}
              >
                {p.name}
              </button>
            ))}
          </div>
        </div>

        {/* Manual Coordinate Form */}
        <div className="mt-5 grid grid-cols-1 gap-4 sm:grid-cols-4">
          <div>
            <label className="block text-xs font-medium text-charcoal-muted mb-1">
              Latitude (°N: 28.25 – 29.00)
            </label>
            <input
              type="number"
              step="0.0001"
              value={lat}
              onChange={(e) => setLat(parseFloat(e.target.value))}
              className="w-full rounded-md border border-[#E5E5DF] bg-[#FAFAF7] px-3 py-2 text-xs font-mono text-charcoal focus:border-brand-green focus:bg-white focus:outline-none transition-colors"
            />
          </div>

          <div>
            <label className="block text-xs font-medium text-charcoal-muted mb-1">
              Longitude (°E: 76.75 – 77.60)
            </label>
            <input
              type="number"
              step="0.0001"
              value={lon}
              onChange={(e) => setLon(parseFloat(e.target.value))}
              className="w-full rounded-md border border-[#E5E5DF] bg-[#FAFAF7] px-3 py-2 text-xs font-mono text-charcoal focus:border-brand-green focus:bg-white focus:outline-none transition-colors"
            />
          </div>

          <div>
            <label className="block text-xs font-medium text-charcoal-muted mb-1">
              Spatial Estimation Model
            </label>
            <select
              value={modelType}
              onChange={(e) => setModelType(e.target.value)}
              className="w-full rounded-md border border-[#E5E5DF] bg-[#FAFAF7] px-3 py-2 text-xs text-charcoal focus:border-brand-green focus:bg-white focus:outline-none transition-colors"
            >
              <option value="graphsage">GraphSAGE (Spatial Inductive)</option>
              <option value="gat">Graph Attention Network (GAT)</option>
              <option value="gcn">Graph Convolutional Network (GCN)</option>
              <option value="stgnn">Spatiotemporal GNN</option>
            </select>
          </div>

          <div className="flex items-end">
            <button
              onClick={() => handlePredict()}
              disabled={loading}
              className="w-full flex items-center justify-center gap-2 rounded-md bg-brand-green px-4 py-2 text-xs font-medium text-white transition-colors hover:bg-brand-greenDark disabled:opacity-50 shadow-[0_1px_2px_rgba(0,0,0,0.04)]"
            >
              <Share2 className="h-3.5 w-3.5" />
              <span>{loading ? 'Estimating...' : 'Estimate Air Quality'}</span>
            </button>
          </div>
        </div>
      </div>

      {error && (
        <div className="rounded-xl border border-[#F5C2C2] bg-[#FCEEEE] p-4 text-xs text-[#8A2424]">
          {error}
        </div>
      )}

      {/* Prediction Output & Confidence Categorization */}
      {prediction && (
        <div className="space-y-6">
          {/* Narrative Summary */}
          <div className="rounded-xl border border-[#E5E5DF] bg-white p-4 shadow-[0_1px_3px_rgba(0,0,0,0.02)]">
            <div className="flex items-center gap-2">
              <span className="text-xs font-semibold uppercase tracking-wider text-charcoal-muted">
                Spatial Estimate Summary
              </span>
              <span className="rounded bg-[#EAF4F1] px-2 py-0.5 text-[11px] font-medium text-[#285D52] border border-[#CDE5DF]">
                Confidence: {prediction.target_location.confidence_rating}
              </span>
            </div>
            <p className="mt-1.5 text-xs text-charcoal leading-relaxed">
              At coordinate <strong className="font-semibold">{lat.toFixed(4)}°N, {lon.toFixed(4)}°E</strong>, estimated
              PM2.5 is <strong className="font-semibold">{prediction.pm2_5.point_estimate.toFixed(1)} µg/m³</strong>.
              The nearest physical monitoring station is{' '}
              <strong className="font-semibold">{prediction.nearest_monitoring_station.name}</strong>, located{' '}
              <strong className="font-semibold">{prediction.target_location.distance_to_nearest_monitor_km} km</strong> away.
            </p>
          </div>

          <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
            <MetricCard
              title="Estimated PM2.5"
              value={prediction.pm2_5.point_estimate.toFixed(1)}
              unit="µg/m³"
              subtitle={`90% Interval: [${prediction.pm2_5.lower_bound} – ${prediction.pm2_5.upper_bound}]`}
              trend={{
                value: `Confidence: ${prediction.target_location.confidence_rating}`,
                isPositive: prediction.target_location.confidence_rating === 'HIGH',
              }}
              badge={
                <span className="rounded bg-[#EAF4F1] px-2 py-0.5 text-[10px] font-mono text-[#285D52] border border-[#CDE5DF]">
                  Model Estimate
                </span>
              }
            />

            <MetricCard
              title="Estimated PM10"
              value={prediction.pm10.point_estimate.toFixed(1)}
              unit="µg/m³"
              subtitle={`90% Interval: [${prediction.pm10.lower_bound} – ${prediction.pm10.upper_bound}]`}
              trend={{ value: 'Coarse dust fraction', isNeutral: true }}
              badge={
                <span className="rounded bg-[#EEF4F8] px-2 py-0.5 text-[10px] font-mono text-[#50728F] border border-[#D5E3EC]">
                  Coarse Dust
                </span>
              }
            />

            <MetricCard
              title="Nearest Physical Station"
              value={`${prediction.target_location.distance_to_nearest_monitor_km} km`}
              subtitle={prediction.nearest_monitoring_station.name}
              trend={{
                value: prediction.nearest_monitoring_station.classification,
                isNeutral: true,
              }}
              badge={
                <span className="rounded bg-[#F2F2EC] px-2 py-0.5 text-[10px] font-mono text-charcoal-muted border border-[#E5E5DF]">
                  Ground Truth
                </span>
              }
            />
          </div>

          {/* Model Comparison Breakdown: Physical vs Interpolated vs GNN */}
          {prediction.model_comparison && (
            <div className="rounded-xl border border-[#E5E5DF] bg-white p-6 shadow-[0_1px_3px_rgba(0,0,0,0.02)]">
              <h3 className="text-sm font-semibold tracking-tight text-charcoal mb-1">
                Spatial Methodology Comparison
              </h3>
              <p className="text-xs text-charcoal-muted mb-5">
                Comparison between graph neural network estimation, inverse distance weighting, and gradient boosting
              </p>

              <div className="grid grid-cols-1 gap-4 md:grid-cols-3">
                {/* Method 1: GNN */}
                <div className="rounded-xl border border-[#CDE5DF] bg-[#FAFDFB] p-4 space-y-2.5">
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-semibold text-[#285D52]">
                      Graph Neural Network
                    </span>
                    <span className="rounded bg-[#EAF4F1] px-2 py-0.5 text-[10px] font-mono text-[#285D52] border border-[#CDE5DF]">
                      MAE: {prediction.model_comparison.graphsage_gnn.mae}
                    </span>
                  </div>
                  <div className="flex items-baseline gap-2">
                    <span className="font-mono text-2xl font-bold text-charcoal">
                      {prediction.model_comparison.graphsage_gnn.pm2_5}
                    </span>
                    <span className="text-xs text-charcoal-muted">µg/m³ PM2.5</span>
                  </div>
                  <p className="text-xs text-charcoal-muted leading-relaxed">
                    Learns topological relationships between stations, incorporating wind alignment and urban road density.
                  </p>
                </div>

                {/* Method 2: IDW */}
                <div className="rounded-xl border border-[#E5E5DF] bg-[#FAFAF7] p-4 space-y-2.5">
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-semibold text-charcoal">
                      Inverse Distance Weighting
                    </span>
                    <span className="rounded bg-white px-2 py-0.5 text-[10px] font-mono text-charcoal-muted border border-[#E5E5DF]">
                      MAE: {prediction.model_comparison.idw_interpolation.mae}
                    </span>
                  </div>
                  <div className="flex items-baseline gap-2">
                    <span className="font-mono text-2xl font-bold text-charcoal">
                      {prediction.model_comparison.idw_interpolation.pm2_5}
                    </span>
                    <span className="text-xs text-charcoal-muted">µg/m³ PM2.5</span>
                  </div>
                  <p className="text-xs text-charcoal-muted leading-relaxed">
                    Deterministic geometric interpolation decaying with Euclidean/Haversine distance squared.
                  </p>
                </div>

                {/* Method 3: Spatial XGBoost */}
                <div className="rounded-xl border border-[#E5E5DF] bg-[#FAFAF7] p-4 space-y-2.5">
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-semibold text-charcoal">
                      Spatial Gradient Boosting
                    </span>
                    <span className="rounded bg-white px-2 py-0.5 text-[10px] font-mono text-charcoal-muted border border-[#E5E5DF]">
                      MAE: {prediction.model_comparison.spatial_xgboost.mae}
                    </span>
                  </div>
                  <div className="flex items-baseline gap-2">
                    <span className="font-mono text-2xl font-bold text-charcoal">
                      {prediction.model_comparison.spatial_xgboost.pm2_5}
                    </span>
                    <span className="text-xs text-charcoal-muted">µg/m³ PM2.5</span>
                  </div>
                  <p className="text-xs text-charcoal-muted leading-relaxed">
                    Tree-based gradient boosted regression conditioned on geographic coordinates and road factors.
                  </p>
                </div>
              </div>
            </div>
          )}

          {/* Supporting Monitoring Stations contributing to this prediction */}
          {prediction.supporting_stations && prediction.supporting_stations.length > 0 && (
            <div className="rounded-xl border border-[#E5E5DF] bg-white p-6 shadow-[0_1px_3px_rgba(0,0,0,0.02)]">
              <h3 className="text-sm font-semibold tracking-tight text-charcoal mb-1">
                Surrounding Physical Station Anchors
              </h3>
              <p className="text-xs text-charcoal-muted mb-4">
                Continuous monitoring stations weighted by proximity to target coordinates ({lat.toFixed(4)}°N, {lon.toFixed(4)}°E)
              </p>

              <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-4">
                {prediction.supporting_stations.map((st) => (
                  <div key={st.station_id} className="rounded-lg border border-[#E5E5DF] bg-[#FAFAF7] p-3 space-y-1.5">
                    <div className="font-medium text-xs text-charcoal">{st.name}</div>
                    <div className="flex items-center justify-between font-mono text-[11px]">
                      <span className="text-charcoal-muted">Distance:</span>
                      <span className="text-charcoal font-semibold">{st.distance_km} km</span>
                    </div>
                    <div className="flex items-center justify-between font-mono text-[11px]">
                      <span className="text-charcoal-muted">Graph Weight:</span>
                      <span className="text-charcoal font-semibold">{(st.weight * 100).toFixed(1)}%</span>
                    </div>
                    <div className="flex items-center justify-between font-mono text-[11px] pt-1 border-t border-[#E5E5DF]">
                      <span className="text-charcoal-muted">Observed PM2.5:</span>
                      <span className="text-brand-green font-semibold">{st.pm2_5} µg/m³</span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
};
