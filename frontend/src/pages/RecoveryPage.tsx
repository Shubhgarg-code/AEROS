import React, { useState, useEffect } from 'react';
import {
  Clock,
  Wind,
  Droplets,
  AlertCircle,
  HelpCircle,
  ArrowRight,
  TrendingDown,
  CheckCircle,
  Info,
} from 'lucide-react';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  ReferenceLine,
} from 'recharts';
import { apiClient } from '../api/client';
import { RecoveryData } from '../types';
import { MetricCard } from '../components/MetricCard';
import { DisclaimerBanner } from '../components/DisclaimerBanner';

export const RecoveryPage: React.FC = () => {
  const [selectedThreshold, setSelectedThreshold] = useState<number>(60.0);
  const [windSpeed, setWindSpeed] = useState<number>(2.2);
  const [rainfall, setRainfall] = useState<number>(0.0);

  const [recoveryData, setRecoveryData] = useState<RecoveryData | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [showHelper, setShowHelper] = useState<boolean>(false);

  // Realistic post-Diwali concentration series (peaking at ~450 µg/m³)
  const defaultPm25Series = [
    85.0, 110.0, 160.0, 240.0, 380.0, 445.0, 420.0, 360.0, 290.0, 230.0, 180.0,
    140.0, 115.0, 95.0, 80.0, 72.0, 68.0, 64.0, 61.0, 58.0, 55.0, 52.0, 49.0, 47.0,
  ];

  const handlePredict = async () => {
    try {
      setLoading(true);
      setError(null);
      const res = await apiClient.predictRecovery({
        pm25_series: defaultPm25Series,
        target_pm25_threshold: selectedThreshold,
        wind_speed_ms: windSpeed,
        rainfall_mm: rainfall,
      });
      setRecoveryData(res);
    } catch (err: any) {
      setError(err.message || 'Recovery prediction failed.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    handlePredict();
  }, [selectedThreshold, windSpeed, rainfall]);

  const recDetail = recoveryData?.pm25_recovery;

  // Generate chart data for the projected relaxation decay curve
  const curveSample = recDetail?.recovery_curve_sample;
  const chartData =
    curveSample?.hours_post_peak.map((h, i) => ({
      hour: `+${h}h`,
      concentration: curveSample.projected_concentrations[i],
      threshold: selectedThreshold,
    })) || [];

  return (
    <div className="space-y-6">
      <DisclaimerBanner type="uncertainty" />

      {/* Explainer Banner */}
      <div className="rounded-xl border border-[#CDE5DF] bg-[#EAF4F1]/60 p-4">
        <div className="flex items-start justify-between">
          <div className="flex items-start gap-2.5">
            <Clock className="h-4 w-4 text-brand-green mt-0.5 shrink-0" />
            <div>
              <h3 className="text-xs font-semibold uppercase tracking-wider text-[#285D52]">
                Atmospheric Recovery Time & Cleanout Rate
              </h3>
              <p className="mt-1 text-xs text-[#285D52]/90 leading-relaxed">
                After severe pollution spikes (like Diwali night or heavy stubble burning episodes), 
                how many hours will nature take to return air back below safe standards? 
                This tool calculates the <strong>particulate relaxation half-life ($t_{1/2}$)</strong> and total clearance duration.
              </p>
            </div>
          </div>
          <button
            onClick={() => setShowHelper(!showHelper)}
            className="text-[11px] font-medium text-brand-green hover:underline shrink-0 ml-3"
          >
            {showHelper ? 'Hide Guide' : 'How it Works'}
          </button>
        </div>

        {showHelper && (
          <div className="mt-3 pt-3 border-t border-[#CDE5DF] grid grid-cols-1 md:grid-cols-3 gap-3 text-xs text-[#285D52]">
            <div className="rounded-lg bg-white/70 p-2.5 border border-[#CDE5DF]">
              <strong>• Relaxation Rate:</strong> Speed at which particulates disperse through wind advection and dry deposition.
            </div>
            <div className="rounded-lg bg-white/70 p-2.5 border border-[#CDE5DF]">
              <strong>• Half-Life ($t_{1/2}$):</strong> Time in hours required for the atmosphere to cut pollutant density in half.
            </div>
            <div className="rounded-lg bg-white/70 p-2.5 border border-[#CDE5DF]">
              <strong>• Rain Scavenging:</strong> Rainfall washes airborne dust down to the surface, accelerating recovery.
            </div>
          </div>
        )}
      </div>

      {/* Control Configuration Panel */}
      <div className="rounded-xl border border-[#E5E5DF] bg-white p-6 shadow-[0_1px_3px_rgba(0,0,0,0.02)]">
        <div className="border-b border-[#F2F2EC] pb-4">
          <h3 className="text-sm font-semibold tracking-tight text-charcoal">
            Estimated Air Quality Recovery Controls
          </h3>
          <p className="text-xs text-charcoal-muted">
            Calculate atmospheric relaxation rates and projected hours to return below clean air standards
          </p>
        </div>

        <div className="mt-5 grid grid-cols-1 gap-5 sm:grid-cols-3">
          {/* Threshold Preset Selector */}
          <div>
            <label className="block text-xs font-medium text-charcoal-muted mb-1.5">
              Target Air Quality Standard
            </label>
            <div className="grid grid-cols-3 gap-1.5">
              {[
                { label: 'NAAQS (60)', val: 60.0 },
                { label: 'Moderate (90)', val: 90.0 },
                { label: 'WHO (15)', val: 15.0 },
              ].map((t) => (
                <button
                  key={t.val}
                  onClick={() => setSelectedThreshold(t.val)}
                  className={`rounded border py-2 text-xs transition-colors ${
                    selectedThreshold === t.val
                      ? 'border-[#CDE5DF] bg-[#EAF4F1] text-[#285D52] font-semibold'
                      : 'border-[#E5E5DF] bg-[#FAFAF7] text-charcoal-muted hover:bg-white hover:text-charcoal'
                  }`}
                >
                  {t.label}
                </button>
              ))}
            </div>
          </div>

          {/* Wind Speed Ventilation Slider */}
          <div>
            <div className="flex items-center justify-between mb-1.5">
              <label className="text-xs font-medium text-charcoal-muted">
                Surface Wind Speed
              </label>
              <span className="font-mono text-xs text-charcoal font-semibold">{windSpeed.toFixed(1)} m/s</span>
            </div>
            <input
              type="range"
              min="0.8"
              max="7.0"
              step="0.2"
              value={windSpeed}
              onChange={(e) => setWindSpeed(parseFloat(e.target.value))}
              className="w-full accent-[#527D75] cursor-pointer"
            />
            <div className="flex justify-between text-[10px] text-charcoal-muted mt-1">
              <span>0.8 (Stagnant)</span>
              <span>2.5 (Normal)</span>
              <span>7.0 (Rapid Flushing)</span>
            </div>
          </div>

          {/* Precipitation Scavenging */}
          <div>
            <div className="flex items-center justify-between mb-1.5">
              <label className="text-xs font-medium text-charcoal-muted">
                Rainfall Scavenging
              </label>
              <span className="font-mono text-xs text-charcoal font-semibold">{rainfall.toFixed(1)} mm</span>
            </div>
            <input
              type="range"
              min="0.0"
              max="15.0"
              step="1.0"
              value={rainfall}
              onChange={(e) => setRainfall(parseFloat(e.target.value))}
              className="w-full accent-[#527D75] cursor-pointer"
            />
            <div className="flex justify-between text-[10px] text-charcoal-muted mt-1">
              <span>0.0 mm (Dry Settling)</span>
              <span>15.0 mm (Rain Deposition)</span>
            </div>
          </div>
        </div>
      </div>

      {error && (
        <div className="rounded-xl border border-[#F5C2C2] bg-[#FCEEEE] p-4 text-xs text-[#8A2424]">
          {error}
        </div>
      )}

      {/* Recovery Metrics */}
      {recDetail && (
        <>
          {/* Narrative Recovery Briefing */}
          <div className="rounded-xl border border-[#E5E5DF] bg-white p-4 shadow-[0_1px_3px_rgba(0,0,0,0.02)]">
            <div className="flex items-center gap-2">
              <span className="text-xs font-semibold uppercase tracking-wider text-charcoal-muted">
                Recovery Outlook
              </span>
              <span className="rounded bg-[#EAF4F1] px-2 py-0.5 text-[11px] font-medium text-[#285D52] border border-[#CDE5DF]">
                {recDetail.status}
              </span>
            </div>
            <p className="mt-1.5 text-xs text-charcoal leading-relaxed">
              Following the peak of <strong className="font-semibold">{recDetail.peak_value.toFixed(1)} µg/m³</strong>, fine
              particulate levels are projected to recover below the <strong className="font-semibold">{recDetail.target_threshold} µg/m³</strong> threshold
              in approximately <strong className="font-semibold">{recDetail.clearance_hours_from_peak.toFixed(1)} hours</strong> (90%
              interval: {recDetail.confidence_interval_90[0]}h – {recDetail.confidence_interval_90[1]}h) under current
              wind conditions of {windSpeed} m/s. The particulate relaxation half-life is {recDetail.half_life_hours.toFixed(1)} hours.
            </p>
          </div>

          <div className="grid grid-cols-1 gap-4 sm:grid-cols-4">
            <MetricCard
              title="Estimated Time to Clear"
              value={
                recDetail.clearance_hours_from_peak > 0
                  ? `${recDetail.clearance_hours_from_peak.toFixed(1)}h`
                  : '0h'
              }
              subtitle={
                recDetail.recovery_achieved_within_horizon
                  ? `Crosses standard at Hour +${recDetail.clearance_hours_from_start}`
                  : 'Analytically Extrapolated'
              }
              trend={{
                value: recDetail.status,
                isPositive: recDetail.recovery_achieved_within_horizon,
              }}
            />

            <MetricCard
              title="90% Confidence Interval"
              value={`[${recDetail.confidence_interval_90[0]}h – ${recDetail.confidence_interval_90[1]}h]`}
              subtitle="Calibrated empirical residual range"
              trend={{ value: 'Confidence: 90%', isNeutral: true }}
            />

            <MetricCard
              title="Relaxation Half-Life (t½)"
              value={`${recDetail.half_life_hours.toFixed(1)}h`}
              subtitle="Time to reduce peak by 50%"
              trend={{
                value: `Ventilation: ${(windSpeed * 3.6).toFixed(1)} km/h`,
                isNeutral: true,
              }}
            />

            <MetricCard
              title="Target Threshold"
              value={`${recDetail.target_threshold}`}
              unit="µg/m³"
              subtitle={`Peak: ${recDetail.peak_value.toFixed(1)} µg/m³`}
              trend={{
                value: `${((1 - recDetail.target_threshold / recDetail.peak_value) * 100).toFixed(0)}% Reduction Required`,
                isNeutral: true,
              }}
            />
          </div>
        </>
      )}

      {/* Recovery Curve Chart */}
      <div className="rounded-xl border border-[#E5E5DF] bg-white p-6 shadow-[0_1px_3px_rgba(0,0,0,0.02)]">
        <div className="flex flex-wrap items-center justify-between gap-4 border-b border-[#F2F2EC] pb-4 mb-4">
          <div>
            <h3 className="text-sm font-semibold tracking-tight text-charcoal">
              Post-Peak Particulate Relaxation Trajectory
            </h3>
            <p className="text-xs text-charcoal-muted">
              Projected exponential decay curve indicating clearance below the {selectedThreshold} µg/m³ threshold
            </p>
          </div>

          <div className="flex items-center gap-4 text-xs">
            <span className="flex items-center gap-1.5 text-charcoal">
              <span className="h-2 w-2 rounded-full bg-brand-green" />
              Projected PM2.5 Decay
            </span>
            <span className="flex items-center gap-1.5 text-[#C26738]">
              <span className="h-0.5 w-3 bg-[#C26738]" />
              Target Standard ({selectedThreshold} µg/m³)
            </span>
          </div>
        </div>

        <div className="h-72 w-full">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={chartData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#F0F0EB" vertical={false} />
              <XAxis dataKey="hour" stroke="#8C959D" fontSize={11} tickLine={false} />
              <YAxis stroke="#8C959D" fontSize={11} tickLine={false} />
              <ReferenceLine y={selectedThreshold} stroke="#C26738" strokeDasharray="4 4" />
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
              <Line
                type="monotone"
                dataKey="concentration"
                stroke="#527D75"
                strokeWidth={2.5}
                dot={false}
                name="Projected PM2.5 (µg/m³)"
              />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </div>
    </div>
  );
};
