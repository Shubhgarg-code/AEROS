import React, { useState, useEffect } from 'react';
import {
  Sparkles,
  Sliders,
  TrendingDown,
  TrendingUp,
  AlertTriangle,
  ArrowRight,
  ShieldAlert,
  Play,
  RotateCcw,
  CheckCircle2,
  HelpCircle,
  Award,
} from 'lucide-react';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend,
  ReferenceLine,
} from 'recharts';
import { apiClient } from '../api/client';
import { ScenarioSimulationData, ScenarioType } from '../types';
import { MetricCard } from '../components/MetricCard';
import { DisclaimerBanner } from '../components/DisclaimerBanner';

export const DiwaliSimulatorPage: React.FC = () => {
  const [selectedScenario, setSelectedScenario] = useState<ScenarioType>('combined_mitigation');
  const [durationHours, setDurationHours] = useState<number>(72);

  const [baselineData, setBaselineData] = useState<ScenarioSimulationData | null>(null);
  const [scenarioData, setScenarioData] = useState<ScenarioSimulationData | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [showHelper, setShowHelper] = useState<boolean>(false);

  const scenarioOptions: Array<{
    type: ScenarioType;
    name: string;
    description: string;
    firecrackerImpact: string;
    trafficImpact: string;
    badge: string;
    badgeClass: string;
  }> = [
    {
      type: 'combined_mitigation',
      name: 'Combined Policy (Ban + Vehicle Curbs)',
      description: 'Comprehensive mitigation combining fireworks restrictions (-70%) with 40% traffic rationing.',
      firecrackerImpact: '-70% Fireworks',
      trafficImpact: '-40% Vehicular Traffic',
      badge: 'Recommended',
      badgeClass: 'bg-[#EAF4F1] text-[#285D52] border-[#CDE5DF]',
    },
    {
      type: 'firecracker_reduction',
      name: 'Firecracker Ban Compliance',
      description: 'Enforcement of pyrotechnic restrictions achieving a 70% emission reduction on Diwali night.',
      firecrackerImpact: '-70% Fireworks',
      trafficImpact: 'Normal Festive Traffic',
      badge: 'High Impact',
      badgeClass: 'bg-[#EAF4F1] text-[#285D52] border-[#CDE5DF]',
    },
    {
      type: 'traffic_reduction',
      name: 'Odd-Even Vehicle Rationing',
      description: 'Vehicle license plate rationing and heavy commercial vehicle entry curbs.',
      firecrackerImpact: 'Unrestricted Fireworks',
      trafficImpact: '-40% Vehicular Traffic',
      badge: 'Moderate Impact',
      badgeClass: 'bg-[#FDF6E9] text-[#865914] border-[#F5E2BE]',
    },
    {
      type: 'weather_flushing',
      name: 'Atmospheric Ventilation & High Wind',
      description: 'Synoptic weather system with elevated surface winds (+3.5 m/s) and deeper boundary layer.',
      firecrackerImpact: 'Normal Baseline',
      trafficImpact: 'Normal Baseline',
      badge: 'Natural Flushing',
      badgeClass: 'bg-[#EEF4F8] text-[#50728F] border-[#D5E3EC]',
    },
    {
      type: 'firecracker_increase',
      name: 'Severe Firecracker Surge (+100%)',
      description: 'Hypothetical worst-case scenario with doubling of fireworks emissions.',
      firecrackerImpact: '+100% Fireworks',
      trafficImpact: 'Normal Festive Traffic',
      badge: 'Worst Case',
      badgeClass: 'bg-[#FCEEEE] text-[#8A2424] border-[#F5C2C2]',
    },
    {
      type: 'traffic_increase',
      name: 'Post-Diwali Traffic Gridlock (+30%)',
      description: 'Severe post-festival commercial congestion and vehicle backlog.',
      firecrackerImpact: 'Normal Baseline',
      trafficImpact: '+30% Vehicular Traffic',
      badge: 'Stress Test',
      badgeClass: 'bg-[#FDF0E9] text-[#873A16] border-[#F6D0BA]',
    },
  ];

  const runSimulation = async () => {
    try {
      setLoading(true);
      setError(null);

      // Fetch baseline scenario and chosen scenario concurrently
      const [baseRes, scenRes] = await Promise.all([
        apiClient.simulateScenario({
          scenario_type: 'baseline',
          duration_hours: durationHours,
        }),
        apiClient.simulateScenario({
          scenario_type: selectedScenario,
          duration_hours: durationHours,
        }),
      ]);

      setBaselineData(baseRes);
      setScenarioData(scenRes);
    } catch (err: any) {
      setError(err.message || 'Counterfactual simulation failed.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    runSimulation();
  }, [selectedScenario, durationHours]);

  // Combine baseline and scenario curves for Recharts
  const comparisonChartData =
    baselineData?.hourly_mean_pm25_series.map((baseVal, idx) => {
      const scenVal = scenarioData?.hourly_mean_pm25_series[idx] || 0;
      return {
        hour: `+${idx}h`,
        baseline_pm25: baseVal,
        scenario_pm25: scenVal,
        delta: Math.round(scenVal - baseVal),
        naaqs: 60,
      };
    }) || [];

  const deltaPeak =
    scenarioData && baselineData
      ? Math.round(scenarioData.peak_pm25 - baselineData.peak_pm25)
      : 0;

  const deltaPeakPct =
    scenarioData && baselineData
      ? ((deltaPeak / baselineData.peak_pm25) * 100).toFixed(1)
      : '0.0';

  const deltaExposurePct =
    scenarioData && baselineData
      ? (
          ((scenarioData.cumulative_exposure_pm25 - baselineData.cumulative_exposure_pm25) /
            baselineData.cumulative_exposure_pm25) *
          100
        ).toFixed(1)
      : '0.0';

  const isReduction = deltaPeak <= 0;

  return (
    <div className="space-y-6">
      <DisclaimerBanner
        type="scenario"
        customMessage="Scenario results are model-based estimates under hypothetical assumptions and are not guaranteed real-world outcomes."
      />

      {/* Explainer Banner */}
      <div className="rounded-xl border border-[#CDE5DF] bg-[#EAF4F1]/60 p-4">
        <div className="flex items-start justify-between">
          <div className="flex items-start gap-2.5">
            <Sparkles className="h-4 w-4 text-[#C48A2C] mt-0.5 shrink-0" />
            <div>
              <h3 className="text-xs font-semibold uppercase tracking-wider text-[#285D52]">
                What-if Policy Sandbox: Test Decisions Before Enforcing Them
              </h3>
              <p className="mt-1 text-xs text-[#285D52]/90 leading-relaxed">
                Click any policy card below to immediately see how it alters the post-Diwali air pollution trajectory 
                compared to <strong>Business As Usual (the grey dotted line)</strong>. 
                Evaluate emission reductions, peak flattening, and avoided health exposure.
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
              <strong>• Grey Dotted Line:</strong> Historical Business-As-Usual (BAU) baseline during Diwali night.
            </div>
            <div className="rounded-lg bg-white/70 p-2.5 border border-[#CDE5DF]">
              <strong>• Solid Green Line:</strong> Projected pollution curve if the selected policy is implemented.
            </div>
            <div className="rounded-lg bg-white/70 p-2.5 border border-[#CDE5DF]">
              <strong>• Cumulative Impact:</strong> Calculates the total volume of toxic smoke avoided over the full window.
            </div>
          </div>
        )}
      </div>

      {/* Scenario Control Configuration */}
      <div className="rounded-xl border border-[#E5E5DF] bg-white p-6 shadow-[0_1px_3px_rgba(0,0,0,0.02)]">
        <div className="flex flex-wrap items-center justify-between gap-4 border-b border-[#F2F2EC] pb-4">
          <div>
            <h3 className="text-sm font-semibold tracking-tight text-charcoal">
              Select an Environmental Policy Intervention
            </h3>
            <p className="text-xs text-charcoal-muted mt-1">
              Click any scenario card below to simulate its impact in real-time:
            </p>
          </div>

          <div className="flex items-center gap-3">
            <select
              value={durationHours}
              onChange={(e) => setDurationHours(parseInt(e.target.value))}
              className="rounded-md border border-[#E5E5DF] bg-[#FAFAF7] px-3 py-1.5 text-xs text-charcoal focus:border-brand-green focus:bg-white focus:outline-none transition-colors"
            >
              <option value="24">24-Hour Acute Window</option>
              <option value="48">48-Hour Event Window</option>
              <option value="72">72-Hour Full Cycle Window</option>
            </select>

            <button
              onClick={runSimulation}
              disabled={loading}
              className="flex items-center gap-1.5 rounded-md bg-brand-green px-4 py-1.5 text-xs font-medium text-white transition-colors hover:bg-brand-greenDark disabled:opacity-50 shadow-[0_1px_2px_rgba(0,0,0,0.04)]"
            >
              <Play className="h-3.5 w-3.5" />
              <span>{loading ? 'Simulating...' : 'Recalculate'}</span>
            </button>
          </div>
        </div>

        {/* Scenario Selection Grid */}
        <div className="mt-5 grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-3">
          {scenarioOptions.map((opt) => {
            const isSelected = selectedScenario === opt.type;
            return (
              <div
                key={opt.type}
                onClick={() => setSelectedScenario(opt.type)}
                className={`cursor-pointer rounded-xl border p-4 transition-all duration-150 ${
                  isSelected
                    ? 'border-brand-green bg-[#FAFDFB] shadow-sm ring-1 ring-brand-green/20'
                    : 'border-[#E5E5DF] bg-[#FAFAF7] hover:border-[#D1D1C7] hover:bg-white'
                }`}
              >
                <div className="flex items-start justify-between">
                  <h4
                    className={`text-xs font-semibold ${
                      isSelected ? 'text-[#285D52]' : 'text-charcoal'
                    }`}
                  >
                    {opt.name}
                  </h4>
                  <span className={`rounded px-1.5 py-0.5 text-[10px] font-medium border ${opt.badgeClass}`}>
                    {opt.badge}
                  </span>
                </div>
                <p className="mt-1.5 text-xs text-charcoal-muted leading-relaxed">
                  {opt.description}
                </p>
                <div className="mt-3 flex items-center justify-between border-t border-[#E5E5DF]/60 pt-2 text-[10px] text-charcoal-muted font-mono">
                  <span className="font-medium text-charcoal">{opt.firecrackerImpact}</span>
                  <span>{opt.trafficImpact}</span>
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {error && (
        <div className="rounded-xl border border-[#F5C2C2] bg-[#FCEEEE] p-4 text-xs text-[#8A2424]">
          {error}
        </div>
      )}

      {/* Before vs After Impact Metrics */}
      {baselineData && scenarioData && (
        <>
          {/* Narrative Scenario Briefing */}
          <div className="rounded-xl border border-[#E5E5DF] bg-white p-5 shadow-[0_1px_3px_rgba(0,0,0,0.02)]">
            <div className="flex items-center justify-between">
              <span className="text-xs font-semibold uppercase tracking-wider text-charcoal-muted">
                Simulation Outcome: {scenarioData.scenario_name}
              </span>
              <span
                className={`rounded px-2.5 py-0.5 text-xs font-medium border ${
                  isReduction
                    ? 'bg-[#EAF4F1] text-[#285D52] border-[#CDE5DF]'
                    : 'bg-[#FDF1EB] text-[#8C431F] border-[#F6D0BE]'
                }`}
              >
                {isReduction ? `Peak Reduced by ${Math.abs(Number(deltaPeakPct))}%` : `Peak Increased by ${deltaPeakPct}%`}
              </span>
            </div>
            <p className="mt-2 text-sm text-charcoal leading-relaxed">
              Under <strong className="font-semibold text-charcoal">{scenarioData.scenario_name}</strong>, citywide peak PM2.5 is
              estimated at <strong className="font-semibold text-brand-green">{scenarioData.peak_pm25.toFixed(1)} µg/m³</strong> compared to{' '}
              <strong className="font-semibold">{baselineData.peak_pm25.toFixed(1)} µg/m³</strong> under baseline conditions—yielding
              a <strong className="font-semibold">{Math.abs(Number(deltaExposurePct))}% {isReduction ? 'reduction' : 'increase'}</strong> in cumulative
              particulate exposure over {durationHours} hours.
            </p>
          </div>

          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
            <MetricCard
              title="Baseline Peak PM2.5"
              value={baselineData.peak_pm25.toFixed(1)}
              unit="µg/m³"
              subtitle={`Occurs at Hour +${baselineData.peak_hour}h`}
              trend={{ value: 'Business as Usual', isNeutral: true }}
            />

            <MetricCard
              title="Scenario Peak PM2.5"
              value={scenarioData.peak_pm25.toFixed(1)}
              unit="µg/m³"
              subtitle={`Occurs at Hour +${scenarioData.peak_hour}h (${scenarioData.peak_hour - baselineData.peak_hour >= 0 ? '+' : ''}${scenarioData.peak_hour - baselineData.peak_hour}h shift)`}
              trend={{
                value: `${deltaPeak > 0 ? '+' : ''}${deltaPeak} µg/m³ (${deltaPeakPct}%)`,
                isPositive: isReduction,
              }}
            />

            <MetricCard
              title="Cumulative Exposure Impact"
              value={`${deltaExposurePct}%`}
              subtitle="Integral particulate burden"
              trend={{
                value: isReduction ? 'Exposure Avoided' : 'Excess Exposure',
                isPositive: isReduction,
              }}
            />

            <MetricCard
              title="Population Exposure Index"
              value={scenarioData.population_weighted_exposure_index.toFixed(1)}
              subtitle={`Baseline: ${baselineData.population_weighted_exposure_index.toFixed(1)}`}
              trend={{
                value: `${(scenarioData.population_weighted_exposure_index - baselineData.population_weighted_exposure_index).toFixed(1)} pts`,
                isPositive: isReduction,
              }}
            />
          </div>
        </>
      )}

      {/* Before-and-After Concentration Timeline Chart */}
      <div className="rounded-xl border border-[#E5E5DF] bg-white p-6 shadow-[0_1px_3px_rgba(0,0,0,0.02)]">
        <div className="flex flex-wrap items-center justify-between gap-4 border-b border-[#F2F2EC] pb-4 mb-4">
          <div>
            <h3 className="text-sm font-semibold tracking-tight text-charcoal">
              Timeline Comparison: Baseline vs. Selected Policy
            </h3>
            <p className="text-xs text-charcoal-muted">
              Citywide mean PM2.5 response curves across the {durationHours}-hour simulation horizon
            </p>
          </div>

          <div className="flex items-center gap-4 text-xs">
            <span className="flex items-center gap-1.5 text-charcoal-muted">
              <span className="h-0.5 w-3 bg-[#8C959D]" />
              Baseline (BAU - No Policy)
            </span>
            <span className="flex items-center gap-1.5 text-charcoal font-medium">
              <span className="h-2 w-2 rounded-full bg-brand-green" />
              {scenarioData?.scenario_name || 'Selected Scenario'}
            </span>
            <span className="flex items-center gap-1.5 text-[#C26738]">
              <span className="h-0.5 w-3 bg-[#C26738]" />
              Safe Limit (60 µg/m³)
            </span>
          </div>
        </div>

        <div className="h-80 w-full">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={comparisonChartData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
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
              <Line
                type="monotone"
                dataKey="baseline_pm25"
                stroke="#8C959D"
                strokeWidth={2}
                strokeDasharray="4 4"
                dot={false}
                name="Baseline PM2.5 (µg/m³)"
              />
              <Line
                type="monotone"
                dataKey="scenario_pm25"
                stroke="#527D75"
                strokeWidth={2.5}
                dot={false}
                name="Scenario PM2.5 (µg/m³)"
              />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </div>
    </div>
  );
};
