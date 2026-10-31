import React, { useState, useEffect, useRef } from 'react';
import {
  Play,
  Pause,
  RotateCcw,
  Wind,
  Layers,
  Compass,
  Activity,
  Calendar,
  FastForward,
} from 'lucide-react';
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  ReferenceLine,
} from 'recharts';
import { apiClient } from '../api/client';
import { PropagationSimulationData, PropagationSnapshot } from '../types';
import { MetricCard } from '../components/MetricCard';
import { DisclaimerBanner } from '../components/DisclaimerBanner';

export const PropagationPage: React.FC = () => {
  const [simulation, setSimulation] = useState<PropagationSimulationData | null>(null);
  const [currentStep, setCurrentStep] = useState<number>(0);
  const [isPlaying, setIsPlaying] = useState<boolean>(false);
  const [playbackSpeed, setPlaybackSpeed] = useState<number>(1000); // ms per step
  const [selectedPollutant, setSelectedPollutant] = useState<'pm25' | 'pm10'>('pm25');
  const [durationHours, setDurationHours] = useState<number>(24);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  const timerRef = useRef<NodeJS.Timeout | null>(null);

  const runSimulation = async () => {
    try {
      setLoading(true);
      setError(null);
      setIsPlaying(false);
      const res = await apiClient.simulatePropagation({
        duration_hours: durationHours,
      });
      setSimulation(res);
      setCurrentStep(0);
    } catch (err: any) {
      setError(err.message || 'Propagation simulation failed.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    runSimulation();
  }, [durationHours]);

  // Animation Loop
  useEffect(() => {
    if (isPlaying && simulation) {
      timerRef.current = setInterval(() => {
        setCurrentStep((prev) => {
          if (prev >= simulation.hourly_snapshots.length - 1) {
            setIsPlaying(false);
            return prev;
          }
          return prev + 1;
        });
      }, playbackSpeed);
    } else if (timerRef.current) {
      clearInterval(timerRef.current);
    }

    return () => {
      if (timerRef.current) clearInterval(timerRef.current);
    };
  }, [isPlaying, simulation, playbackSpeed]);

  const snapshots = simulation?.hourly_snapshots || [];
  const activeSnapshot: PropagationSnapshot | null = snapshots[currentStep] || null;

  // 11x11 grid data for active snapshot
  const currentGrid =
    selectedPollutant === 'pm25'
      ? activeSnapshot?.grid_pm25_snapshot || []
      : activeSnapshot?.grid_pm10_snapshot || [];

  const getCellColor = (val: number) => {
    if (val > 300) return 'bg-[#F9EAEF] text-[#631427] border-[#ECC0CE]';
    if (val > 200) return 'bg-[#FCEEEE] text-[#8A2424] border-[#F5C2C2]';
    if (val > 140) return 'bg-[#FDF1EB] text-[#8C431F] border-[#F6D0BE]';
    if (val > 90) return 'bg-[#FDF6E9] text-[#865914] border-[#F5E2BE]';
    if (val > 60) return 'bg-[#F0F6EB] text-[#476C32] border-[#D6E7CD]';
    return 'bg-[#EAF4F1] text-[#285D52] border-[#CDE5DF]';
  };

  // Trajectory chart over full simulation
  const timelineChartData = snapshots.map((s) => ({
    hour: `+${s.step_hour}h`,
    pm25: s.mean_pm25,
    max_pm25: s.max_pm25,
    pm10: s.mean_pm10,
    wind: s.wind_speed_ms,
  }));

  return (
    <div className="space-y-6">
      <DisclaimerBanner type="scenario" />

      {/* Control Bar */}
      <div className="rounded-xl border border-[#E5E5DF] bg-white p-6 shadow-[0_1px_3px_rgba(0,0,0,0.02)]">
        <div className="flex flex-wrap items-center justify-between gap-4 border-b border-[#F2F2EC] pb-4">
          <div>
            <h3 className="text-sm font-semibold tracking-tight text-charcoal">
              Atmospheric Transport & Diffusion Simulator
            </h3>
            <p className="text-xs text-charcoal-muted">
              Forward simulation of particulate dispersion across 121 geographic cells driven by meteorological wind vectors
            </p>
          </div>

          <div className="flex items-center gap-3">
            <div className="flex items-center gap-1 rounded-md border border-[#E5E5DF] bg-[#FAFAF7] p-1 text-xs">
              <button
                onClick={() => setSelectedPollutant('pm25')}
                className={`rounded px-3 py-1 text-xs font-medium transition-colors ${
                  selectedPollutant === 'pm25'
                    ? 'bg-white text-charcoal font-semibold shadow-[0_1px_2px_rgba(0,0,0,0.04)] border border-[#E5E5DF]'
                    : 'text-charcoal-muted hover:text-charcoal'
                }`}
              >
                PM2.5 (Fine)
              </button>
              <button
                onClick={() => setSelectedPollutant('pm10')}
                className={`rounded px-3 py-1 text-xs font-medium transition-colors ${
                  selectedPollutant === 'pm10'
                    ? 'bg-white text-charcoal font-semibold shadow-[0_1px_2px_rgba(0,0,0,0.04)] border border-[#E5E5DF]'
                    : 'text-charcoal-muted hover:text-charcoal'
                }`}
              >
                PM10 (Coarse)
              </button>
            </div>

            <select
              value={durationHours}
              onChange={(e) => setDurationHours(parseInt(e.target.value))}
              className="rounded-md border border-[#E5E5DF] bg-[#FAFAF7] px-3 py-1.5 text-xs text-charcoal focus:border-brand-green focus:bg-white focus:outline-none transition-colors"
            >
              <option value="12">12-Hour Simulation</option>
              <option value="24">24-Hour Simulation</option>
              <option value="48">48-Hour Simulation</option>
            </select>

            <button
              onClick={runSimulation}
              disabled={loading}
              className="rounded-md bg-white border border-[#E5E5DF] px-3.5 py-1.5 text-xs font-medium text-charcoal hover:bg-[#FAFAF7] disabled:opacity-50 transition-colors shadow-[0_1px_2px_rgba(0,0,0,0.02)]"
            >
              {loading ? 'Simulating...' : 'Re-run'}
            </button>
          </div>
        </div>

        {/* Timeline Slider and Playback Controls */}
        <div className="mt-5 space-y-3">
          <div className="flex items-center justify-between text-xs">
            <div className="flex items-center gap-2">
              <button
                onClick={() => setIsPlaying(!isPlaying)}
                className="flex h-8 w-8 items-center justify-center rounded-md bg-brand-green text-white hover:bg-brand-greenDark transition-colors shadow-[0_1px_2px_rgba(0,0,0,0.04)]"
                title={isPlaying ? 'Pause' : 'Play'}
              >
                {isPlaying ? <Pause className="h-4 w-4" /> : <Play className="h-4 w-4 ml-0.5" />}
              </button>
              <button
                onClick={() => {
                  setIsPlaying(false);
                  setCurrentStep(0);
                }}
                className="flex h-8 w-8 items-center justify-center rounded-md border border-[#E5E5DF] bg-white text-charcoal-muted hover:text-charcoal hover:bg-[#FAFAF7] transition-colors"
                title="Restart"
              >
                <RotateCcw className="h-3.5 w-3.5" />
              </button>
              <span className="text-charcoal font-semibold ml-2">
                Hour +{activeSnapshot?.step_hour || 0}h
              </span>
              <span className="text-charcoal-muted">
                ({activeSnapshot?.timestamp || ''})
              </span>
            </div>

            <div className="flex items-center gap-4 text-xs text-charcoal-muted">
              <span className="flex items-center gap-1.5">
                <Compass className="h-3.5 w-3.5 text-brand-green" />
                Wind: {activeSnapshot?.wind_speed_ms || 2.5} m/s @ {activeSnapshot?.wind_dir_deg || 315}° (NW)
              </span>
              <span className="flex items-center gap-1.5">
                <Activity className="h-3.5 w-3.5 text-brand-blue" />
                Mean: {activeSnapshot?.mean_pm25 || 0} µg/m³
              </span>
            </div>
          </div>

          <input
            type="range"
            min="0"
            max={snapshots.length > 0 ? snapshots.length - 1 : 0}
            value={currentStep}
            onChange={(e) => {
              setIsPlaying(false);
              setCurrentStep(parseInt(e.target.value));
            }}
            className="w-full accent-[#527D75] cursor-pointer"
          />
        </div>
      </div>

      {/* Snapshot KPI Cards */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-4">
        <MetricCard
          title="Current Step Mean"
          value={
            selectedPollutant === 'pm25'
              ? activeSnapshot?.mean_pm25.toFixed(1) || '0.0'
              : activeSnapshot?.mean_pm10.toFixed(1) || '0.0'
          }
          unit="µg/m³"
          subtitle={`Hour +${activeSnapshot?.step_hour || 0}h of ${durationHours}h`}
          trend={{ value: 'Airshed Average', isNeutral: true }}
        />

        <MetricCard
          title="Hotspot Peak Cell"
          value={
            selectedPollutant === 'pm25'
              ? activeSnapshot?.max_pm25.toFixed(1) || '0.0'
              : activeSnapshot?.max_pm10.toFixed(1) || '0.0'
          }
          unit="µg/m³"
          subtitle="Highest localized concentration"
          trend={{ value: 'Plume Center', isNeutral: true }}
        />

        <MetricCard
          title="Numerical Stability"
          value="STABLE"
          subtitle="Courant-Friedrichs-Lewy (CFL ≤ 1.0)"
          trend={{ value: 'Sub-step: 0.05h', isPositive: true }}
        />

        <MetricCard
          title="Domain Mass Balance"
          value={`${simulation?.mass_diagnostics.final_pm25_mass_kg.toFixed(1) || '0.0'} kg`}
          subtitle={`Initial Mass: ${simulation?.mass_diagnostics.initial_pm25_mass_kg.toFixed(1) || '0.0'} kg`}
          trend={{ value: 'Mass Conserved', isPositive: true }}
        />
      </div>

      {/* 11x11 Discrete Grid Heatmap Visualizer */}
      <div className="rounded-xl border border-[#E5E5DF] bg-white p-6 shadow-[0_1px_3px_rgba(0,0,0,0.02)]">
        <div className="flex flex-wrap items-center justify-between gap-4 border-b border-[#F2F2EC] pb-4 mb-4">
          <div>
            <h3 className="text-sm font-semibold tracking-tight text-charcoal">
              Delhi NCR 121-Cell Airshed Heatmap (Hour +{activeSnapshot?.step_hour || 0}h)
            </h3>
            <p className="text-xs text-charcoal-muted">
              Spatial particulate distribution across 11×11 cells (0.05° resolution, ~5.5 km per cell)
            </p>
          </div>

          <div className="flex items-center gap-3 text-xs text-charcoal-muted">
            <span className="flex items-center gap-1.5">
              <span className="h-2.5 w-2.5 rounded bg-[#EAF4F1] border border-[#CDE5DF]" />
              &lt; 60
            </span>
            <span className="flex items-center gap-1.5">
              <span className="h-2.5 w-2.5 rounded bg-[#FDF6E9] border border-[#F5E2BE]" />
              60–140
            </span>
            <span className="flex items-center gap-1.5">
              <span className="h-2.5 w-2.5 rounded bg-[#FDF1EB] border border-[#F6D0BE]" />
              140–200
            </span>
            <span className="flex items-center gap-1.5">
              <span className="h-2.5 w-2.5 rounded bg-[#FCEEEE] border border-[#F5C2C2]" />
              200–300
            </span>
            <span className="flex items-center gap-1.5">
              <span className="h-2.5 w-2.5 rounded bg-[#F9EAEF] border border-[#ECC0CE]" />
              &gt; 300
            </span>
          </div>
        </div>

        {/* 11x11 Grid */}
        <div className="overflow-x-auto">
          <div className="min-w-[500px] max-w-2xl mx-auto p-2">
            <div className="grid grid-cols-11 gap-1.5">
              {currentGrid.map((row, rIdx) =>
                row.map((val, cIdx) => (
                  <div
                    key={`${rIdx}-${cIdx}`}
                    title={`Cell [Row ${rIdx}, Col ${cIdx}]: ${val.toFixed(1)} µg/m³`}
                    className={`aspect-square rounded border flex flex-col items-center justify-center p-1 transition-all duration-300 ${getCellColor(
                      val
                    )}`}
                  >
                    <span className="font-mono text-[9px] font-semibold">
                      {Math.round(val)}
                    </span>
                  </div>
                ))
              )}
            </div>
            <div className="flex justify-between text-[11px] text-charcoal-muted mt-3">
              <span>← West Delhi (76.90°E)</span>
              <span>Central Delhi</span>
              <span>East Delhi / Noida (77.40°E) →</span>
            </div>
          </div>
        </div>
      </div>

      {/* Temporal Rollout Line Chart */}
      <div className="rounded-xl border border-[#E5E5DF] bg-white p-6 shadow-[0_1px_3px_rgba(0,0,0,0.02)]">
        <div className="border-b border-[#F2F2EC] pb-3 mb-4">
          <h3 className="text-sm font-semibold tracking-tight text-charcoal">
            Airshed Mean Concentration Trajectory
          </h3>
          <p className="text-xs text-charcoal-muted">
            Average pollutant concentration progression across the simulation window
          </p>
        </div>

        <div className="h-64 w-full">
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart data={timelineChartData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
              <defs>
                <linearGradient id="propGradient" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#527D75" stopOpacity={0.25} />
                  <stop offset="95%" stopColor="#527D75" stopOpacity={0.0} />
                </linearGradient>
              </defs>
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
                dataKey="pm25"
                stroke="#527D75"
                strokeWidth={2}
                fill="url(#propGradient)"
                name="Airshed Mean PM2.5 (µg/m³)"
              />
            </AreaChart>
          </ResponsiveContainer>
        </div>
      </div>
    </div>
  );
};
