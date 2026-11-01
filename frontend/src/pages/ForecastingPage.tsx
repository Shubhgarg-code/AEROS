import React, { useState, useEffect } from 'react';
import {
  TrendingUp,
  Clock,
  Wind,
  Layers,
  HelpCircle,
  MapPin,
  Calendar,
  AlertCircle,
  CheckCircle2,
} from 'lucide-react';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Area,
  ComposedChart,
  ReferenceLine,
} from 'recharts';
import { apiClient } from '../api/client';
import { AirQualityForecastData, StationDetail } from '../types';
import { MetricCard } from '../components/MetricCard';
import { AQIBadge } from '../components/AQIBadge';
import { DisclaimerBanner } from '../components/DisclaimerBanner';

export const ForecastingPage: React.FC = () => {
  const [stations, setStations] = useState<StationDetail[]>([]);
  const [selectedStationId, setSelectedStationId] = useState<string>('anand_vihar');
  const [selectedHorizon, setSelectedHorizon] = useState<number>(24);
  const [selectedModel, setSelectedModel] = useState<string>('ensemble');
  const [windSpeed, setWindSpeed] = useState<number>(2.5);

  const [forecast, setForecast] = useState<AirQualityForecastData | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [showHelper, setShowHelper] = useState<boolean>(false);

  // Quick popular station shortcuts
  const popularStations = [
    { id: 'anand_vihar', label: 'Anand Vihar (East - Hotspot)' },
    { id: 'punjabi_bagh', label: 'Punjabi Bagh (West)' },
    { id: 'rk_puram', label: 'RK Puram (South)' },
    { id: 'ito', label: 'ITO (Central Traffic)' },
    { id: 'dwarka', label: 'Dwarka (Southwest)' },
  ];

  const horizonPresets = [
    { hours: 6, label: '+6 Hours', desc: 'Evening' },
    { hours: 12, label: '+12 Hours', desc: 'Overnight' },
    { hours: 24, label: '+24 Hours', desc: 'Tomorrow' },
    { hours: 48, label: '+48 Hours', desc: '2 Days' },
    { hours: 72, label: '+72 Hours', desc: '3-Day Outlook' },
  ];

  useEffect(() => {
    const loadStations = async () => {
      try {
        const res = await apiClient.getStations();
        setStations(res.stations);
      } catch (e) {
        console.error('Error fetching stations:', e);
      }
    };
    loadStations();
  }, []);

  const handlePredict = async () => {
    try {
      setLoading(true);
      setError(null);
      const res = await apiClient.predictAirQuality({
        neighborhood_id: selectedStationId,
        horizon_hours: selectedHorizon,
        model_name: selectedModel,
        weather_conditions: { wind_speed: windSpeed },
      });
      setForecast(res);
    } catch (err: any) {
      setError(err.message || 'Failed to fetch air quality prediction.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    handlePredict();
  }, [selectedStationId, selectedHorizon, selectedModel]);

  const timelineData =
    forecast?.hourly_timeline.map((point) => ({
      hour: `+${point.lead_hour}h`,
      timestamp: point.timestamp,
      pm25: point.pm25,
      pm10: point.pm10,
      aqi: point.aqi,
      lower_pm25: point.confidence_interval_90_pm25[0],
      upper_pm25: point.confidence_interval_90_pm25[1],
      naaqs: 60,
    })) || [];

  const currentStation = stations.find((s) => s.neighborhood_id === selectedStationId);

  return (
    <div className="space-y-6">
      <DisclaimerBanner type="uncertainty" />

      {/* Explainer Banner */}
      <div className="rounded-xl border border-[#CDE5DF] bg-[#EAF4F1]/60 p-4">
        <div className="flex items-start justify-between">
          <div className="flex items-start gap-2.5">
            <TrendingUp className="h-4 w-4 text-brand-green mt-0.5 shrink-0" />
            <div>
              <h3 className="text-xs font-semibold uppercase tracking-wider text-[#285D52]">
                72-Hour Predictive Airflow Intelligence
              </h3>
              <p className="mt-1 text-xs text-[#285D52]/90 leading-relaxed">
                Choose any station and time horizon to see hourly pollution projections. The shaded band shows the 
                <strong> 90% confidence interval</strong>, so you can plan outdoor routines, school schedules, 
                and transit timing with clear scientific foresight.
              </p>
            </div>
          </div>
          <button
            onClick={() => setShowHelper(!showHelper)}
            className="text-[11px] font-medium text-brand-green hover:underline shrink-0 ml-3"
          >
            {showHelper ? 'Hide Guide' : 'How to Read'}
          </button>
        </div>

        {showHelper && (
          <div className="mt-3 pt-3 border-t border-[#CDE5DF] grid grid-cols-1 md:grid-cols-3 gap-3 text-xs text-[#285D52]">
            <div className="rounded-lg bg-white/70 p-2.5 border border-[#CDE5DF]">
              <strong>• Green Line:</strong> Predicted PM2.5 level. Keep below 60 µg/m³ for healthy breathing.
            </div>
            <div className="rounded-lg bg-white/70 p-2.5 border border-[#CDE5DF]">
              <strong>• Shaded Zone:</strong> Conformal 90% confidence margin. Wider band means more weather variability.
            </div>
            <div className="rounded-lg bg-white/70 p-2.5 border border-[#CDE5DF]">
              <strong>• Red Dotted Line:</strong> Indian National Standard (NAAQS) safe daily limit of 60 µg/m³.
            </div>
          </div>
        )}
      </div>

      {/* Control Configuration Panel */}
      <div className="rounded-xl border border-[#E5E5DF] bg-white p-6 shadow-[0_1px_3px_rgba(0,0,0,0.02)]">
        <div className="border-b border-[#F2F2EC] pb-4">
          <h3 className="text-sm font-semibold tracking-tight text-charcoal">
            Air Quality Forecasting Controls
          </h3>
          <p className="text-xs text-charcoal-muted">
            Configure target station, forecasting time horizon, and atmospheric dispersion conditions
          </p>
        </div>

        {/* Quick Station Shortcuts */}
        <div className="mt-4">
          <label className="block text-xs font-medium text-charcoal-muted mb-1.5">
            Quick Station Shortcuts:
          </label>
          <div className="flex flex-wrap gap-2">
            {popularStations.map((st) => (
              <button
                key={st.id}
                onClick={() => setSelectedStationId(st.id)}
                className={`flex items-center gap-1.5 rounded-lg border px-3 py-1.5 text-xs transition-all ${
                  selectedStationId === st.id
                    ? 'border-[#CDE5DF] bg-[#EAF4F1] text-[#285D52] font-semibold shadow-sm'
                    : 'border-[#E5E5DF] bg-[#FAFAF7] text-charcoal hover:bg-white'
                }`}
              >
                <MapPin className={`h-3.5 w-3.5 ${selectedStationId === st.id ? 'text-brand-green' : 'text-charcoal-muted'}`} />
                <span>{st.label}</span>
              </button>
            ))}
          </div>
        </div>

        <div className="mt-5 grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-4 pt-4 border-t border-[#F2F2EC]">
          {/* Location Selector */}
          <div>
            <label className="block text-xs font-medium text-charcoal-muted mb-1.5">
              All Monitoring Stations ({stations.length})
            </label>
            <select
              value={selectedStationId}
              onChange={(e) => setSelectedStationId(e.target.value)}
              className="w-full rounded-md border border-[#E5E5DF] bg-[#FAFAF7] px-3 py-2 text-xs text-charcoal focus:border-brand-green focus:bg-white focus:outline-none transition-colors"
            >
              {stations.map((s) => (
                <option key={s.neighborhood_id} value={s.neighborhood_id}>
                  {s.name} ({s.neighborhood_id})
                </option>
              ))}
            </select>
          </div>

          {/* Horizon Selector */}
          <div>
            <label className="block text-xs font-medium text-charcoal-muted mb-1.5">
              Forecast Time Horizon
            </label>
            <div className="grid grid-cols-5 gap-1">
              {horizonPresets.map((h) => (
                <button
                  key={h.hours}
                  onClick={() => setSelectedHorizon(h.hours)}
                  className={`rounded border py-1.5 text-center transition-colors ${
                    selectedHorizon === h.hours
                      ? 'border-[#CDE5DF] bg-[#EAF4F1] text-[#285D52] font-semibold'
                      : 'border-[#E5E5DF] bg-white text-charcoal-muted hover:bg-[#FAFAF7]'
                  }`}
                  title={h.desc}
                >
                  <div className="font-mono text-xs">+{h.hours}h</div>
                  <div className="text-[9px] opacity-75">{h.desc}</div>
                </button>
              ))}
            </div>
          </div>

          {/* Model Family */}
          <div>
            <label className="block text-xs font-medium text-charcoal-muted mb-1.5">
              Predictive AI Model
            </label>
            <select
              value={selectedModel}
              onChange={(e) => setSelectedModel(e.target.value)}
              className="w-full rounded-md border border-[#E5E5DF] bg-[#FAFAF7] px-3 py-2 text-xs text-charcoal focus:border-brand-green focus:bg-white focus:outline-none transition-colors"
            >
              <option value="ensemble">Ensemble (Validation-Weighted, Recommended)</option>
              <option value="xgboost">XGBoost Gradient Boosting</option>
              <option value="transformer">Temporal Transformer</option>
              <option value="lstm">LSTM Recurrent Network</option>
              <option value="gru">GRU Recurrent Network</option>
            </select>
          </div>

          {/* Weather Dispersion Perturbation */}
          <div>
            <div className="flex items-center justify-between mb-1.5">
              <label className="text-xs font-medium text-charcoal-muted">
                Simulated Wind Speed
              </label>
              <span className="font-mono text-xs text-charcoal font-semibold">{windSpeed.toFixed(1)} m/s</span>
            </div>
            <input
              type="range"
              min="0.5"
              max="8.0"
              step="0.5"
              value={windSpeed}
              onChange={(e) => setWindSpeed(parseFloat(e.target.value))}
              className="w-full accent-[#527D75] cursor-pointer"
            />
            <div className="flex justify-between text-[10px] text-charcoal-muted mt-1">
              <span>0.5 (Stagnant)</span>
              <span>2.5 (Normal)</span>
              <span>8.0 (Flushing)</span>
            </div>
          </div>
        </div>
      </div>

      {error && (
        <div className="rounded-xl border border-[#F5C2C2] bg-[#FCEEEE] p-4 text-xs text-[#8A2424]">
          {error}
        </div>
      )}

      {/* Target Horizon Prediction Cards */}
      {forecast && (
        <>
          <div className="rounded-xl border border-[#E5E5DF] bg-white p-5 shadow-[0_1px_3px_rgba(0,0,0,0.02)]">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <span className="text-xs font-semibold uppercase tracking-wider text-charcoal-muted">
                  Forecast Summary for {currentStation?.name || selectedStationId}
                </span>
                <AQIBadge aqi={forecast.predicted_aqi} category={forecast.aqi_category} size="sm" />
              </div>
              <span className="font-mono text-xs text-charcoal-muted">
                Target Horizon: +{forecast.forecast_horizon_hours} Hours Ahead
              </span>
            </div>
            <p className="mt-2 text-sm text-charcoal leading-relaxed">
              At <strong className="font-semibold">+{forecast.forecast_horizon_hours} hours</strong>, air quality at{' '}
              <strong className="font-semibold">{currentStation?.name || selectedStationId}</strong> is projected to be{' '}
              <strong className="font-semibold">{forecast.aqi_category} (AQI {forecast.predicted_aqi})</strong>, with fine particulates
              reaching <strong className="font-semibold text-brand-green">{forecast.predicted_pm25.toFixed(1)} µg/m³</strong> (
              {forecast.predicted_pm25 > 60
                ? `${(forecast.predicted_pm25 / 60).toFixed(1)}x above the 60 µg/m³ daily guideline`
                : 'within the 60 µg/m³ statutory guideline'}
              ).
            </p>
          </div>

          <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
            <MetricCard
              title={`PM2.5 (+${forecast.forecast_horizon_hours}h)`}
              value={forecast.predicted_pm25.toFixed(1)}
              unit="µg/m³"
              subtitle={`90% Interval: [${forecast.confidence_interval_90_pm25[0]} – ${forecast.confidence_interval_90_pm25[1]}]`}
              trend={{
                value: `${forecast.predicted_pm25 > 60 ? 'Above 60 µg/m³ standard' : 'Within NAAQS'}`,
                isPositive: forecast.predicted_pm25 <= 60,
              }}
              badge={
                <span className="rounded bg-[#EAF4F1] px-2 py-0.5 text-[10px] font-mono text-[#285D52] border border-[#CDE5DF]">
                  Fine Particulates
                </span>
              }
            />

            <MetricCard
              title={`PM10 (+${forecast.forecast_horizon_hours}h)`}
              value={forecast.predicted_pm10.toFixed(1)}
              unit="µg/m³"
              subtitle={`90% Interval: [${forecast.confidence_interval_90_pm10[0]} – ${forecast.confidence_interval_90_pm10[1]}]`}
              trend={{
                value: `${forecast.predicted_pm10 > 100 ? 'Above 100 µg/m³ standard' : 'Within NAAQS'}`,
                isPositive: forecast.predicted_pm10 <= 100,
              }}
              badge={
                <span className="rounded bg-[#EEF4F8] px-2 py-0.5 text-[10px] font-mono text-[#50728F] border border-[#D5E3EC]">
                  Coarse Dust
                </span>
              }
            />

            <MetricCard
              title="Projected AQI"
              value={forecast.predicted_aqi}
              subtitle={`Model: ${forecast.model_used}`}
              trend={{
                value: forecast.aqi_category,
                isNeutral: true,
              }}
              badge={<AQIBadge aqi={forecast.predicted_aqi} category={forecast.aqi_category} size="sm" />}
            />
          </div>
        </>
      )}

      {/* Forecast Timeline Chart */}
      <div className="rounded-xl border border-[#E5E5DF] bg-white p-6 shadow-[0_1px_3px_rgba(0,0,0,0.02)]">
        <div className="flex flex-wrap items-center justify-between gap-4 border-b border-[#F2F2EC] pb-4">
          <div>
            <h3 className="text-sm font-semibold tracking-tight text-charcoal">
              Hourly Trajectory & 90% Conformal Confidence Band
            </h3>
            <p className="text-xs text-charcoal-muted">
              Projected concentrations over time with uncertainty bounds calibrated from holdout evaluation
            </p>
          </div>
          <div className="flex items-center gap-4 text-xs">
            <span className="flex items-center gap-1.5 text-charcoal">
              <span className="h-2 w-2 rounded-full bg-brand-green" />
              Predicted PM2.5
            </span>
            <span className="flex items-center gap-1.5 text-charcoal">
              <span className="h-2 w-2 rounded-full bg-brand-blue" />
              Predicted PM10
            </span>
            <span className="flex items-center gap-1.5 text-charcoal-muted">
              <span className="h-2 w-4 rounded bg-[#527D75]/15 border border-[#527D75]/30" />
              90% Confidence Interval
            </span>
            <span className="flex items-center gap-1.5 text-[#C26738]">
              <span className="h-0.5 w-3 bg-[#C26738]" />
              Safe Limit (60 µg/m³)
            </span>
          </div>
        </div>

        <div className="mt-6 h-80 w-full">
          <ResponsiveContainer width="100%" height="100%">
            <ComposedChart data={timelineData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#F0F0EB" vertical={false} />
              <XAxis dataKey="hour" stroke="#8C959D" fontSize={11} tickLine={false} />
              <YAxis stroke="#8C959D" fontSize={11} tickLine={false} />
              <ReferenceLine y={60} stroke="#C26738" strokeDasharray="4 4" />
              <Tooltip
                contentStyle={{
                  backgroundColor: '#FFFFFF',
                  borderColor: '#E5E5DF',
                  borderRadius: '8px',
                  boxShadow: '0 4px 16px rgba(0,0,0,0.06)',
                  fontSize: '12px',
                  color: '#202A30',
                }}
              />
              <Area
                type="monotone"
                dataKey="upper_pm25"
                stroke="transparent"
                fill="#527D75"
                fillOpacity={0.12}
                name="90% Upper Bound"
              />
              <Line
                type="monotone"
                dataKey="pm10"
                stroke="#7899B5"
                strokeWidth={2}
                dot={false}
                name="PM10 (µg/m³)"
              />
              <Line
                type="monotone"
                dataKey="pm25"
                stroke="#527D75"
                strokeWidth={2.5}
                dot={{ r: 2.5, fill: '#527D75' }}
                name="PM2.5 (µg/m³)"
              />
            </ComposedChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Feature Importance & Attribution Breakdown */}
      {forecast && (
        <div className="rounded-xl border border-[#E5E5DF] bg-white p-6 shadow-[0_1px_3px_rgba(0,0,0,0.02)]">
          <h3 className="text-sm font-semibold tracking-tight text-charcoal mb-1">
            Key Environmental Drivers & Influences
          </h3>
          <p className="text-xs text-charcoal-muted mb-4">
            Relative contribution of meteorological and historical factors influencing this forecast
          </p>

          <div className="space-y-3">
            {forecast.feature_importance.map((item, idx) => (
              <div key={idx} className="space-y-1">
                <div className="flex items-center justify-between text-xs">
                  <span className="font-medium text-charcoal">{item.feature}</span>
                  <span className="font-mono text-charcoal-muted">
                    {Math.round(item.importance * 100)}% ({item.impact})
                  </span>
                </div>
                <div className="h-1.5 w-full rounded-full bg-[#F2F2EC] overflow-hidden">
                  <div
                    className="h-full rounded-full bg-brand-green"
                    style={{ width: `${item.importance * 100}%` }}
                  />
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};
