import React, { useState, useEffect } from 'react';
import {
  BarChart3,
  GitCompare,
  TrendingDown,
  TrendingUp,
  Award,
  Layers,
  ArrowRight,
  ShieldCheck,
  CheckCircle,
  Info,
} from 'lucide-react';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend,
  Cell,
} from 'recharts';
import { apiClient } from '../api/client';
import { ScenarioComparisonData, ScenarioComparisonItem } from '../types';
import { MetricCard } from '../components/MetricCard';
import { DisclaimerBanner } from '../components/DisclaimerBanner';

export const ScenarioComparisonPage: React.FC = () => {
  const [data, setData] = useState<ScenarioComparisonData | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [metricView, setMetricView] = useState<'peak' | 'exposure'>('peak');

  const fetchComparison = async () => {
    try {
      setLoading(true);
      setError(null);
      const res = await apiClient.compareScenarios({
        duration_hours: 72,
      });
      setData(res);
    } catch (err: any) {
      setError(err.message || 'Scenario comparison failed.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchComparison();
  }, []);

  if (loading && !data) {
    return (
      <div className="flex h-96 items-center justify-center">
        <div className="flex flex-col items-center gap-3">
          <div className="h-7 w-7 animate-spin rounded-full border-2 border-brand-green border-t-transparent" />
          <span className="text-xs text-charcoal-muted">Benchmarking policy scenarios...</span>
        </div>
      </div>
    );
  }

  const table = data?.comparison_table || [];

  // Identify best policy intervention (lowest cumulative exposure)
  const bestScenario = table.reduce((prev, curr) =>
    curr.cumulative_exposure_pm25 < prev.cumulative_exposure_pm25 ? curr : prev,
    table[0] || {}
  );

  const chartData = table.map((item) => ({
    name: item.scenario_name.split(' (')[0],
    peak: Math.round(item.peak_pm25),
    delta_pct: item.delta_peak_pct,
    exposure: Math.round(item.cumulative_exposure_pm25),
    delta_exp_pct: item.delta_cumulative_exposure_pct,
    isReduction: item.delta_peak_pm25 <= 0,
  }));

  return (
    <div className="space-y-6">
      <DisclaimerBanner type="scenario" />

      {/* Recommended Strategy Callout */}
      {bestScenario && (
        <div className="relative overflow-hidden rounded-xl border border-[#CDE5DF] bg-[#FAFDFB] p-6 shadow-[0_1px_3px_rgba(0,0,0,0.02)]">
          <div className="flex flex-wrap items-center justify-between gap-4">
            <div className="flex items-start gap-3.5">
              <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-[#EAF4F1] text-[#285D52] border border-[#CDE5DF]">
                <Award className="h-5 w-5" />
              </div>
              <div>
                <span className="rounded bg-[#EAF4F1] px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wider text-[#285D52] border border-[#CDE5DF]">
                  Optimal Mitigation Strategy
                </span>
                <h3 className="text-base font-semibold text-charcoal mt-1">
                  {bestScenario.scenario_name}
                </h3>
                <p className="text-xs text-charcoal-muted mt-0.5 leading-relaxed">
                  Achieves the highest public health protection across Delhi NCR over the 72-hour Diwali celebration window.
                </p>
              </div>
            </div>

            <div className="flex items-center gap-6">
              <div className="text-right">
                <span className="text-[10px] text-charcoal-muted block uppercase">Peak PM2.5</span>
                <span className="text-xl font-mono font-semibold text-charcoal">
                  {bestScenario.peak_pm25} µg/m³
                </span>
                <span className="text-xs text-[#3D8B7A] font-medium block">
                  {bestScenario.delta_peak_pct}% vs. Baseline
                </span>
              </div>
              <div className="h-8 w-px bg-[#E5E5DF]" />
              <div className="text-right">
                <span className="text-[10px] text-charcoal-muted block uppercase">Cumulative Exposure</span>
                <span className="text-xl font-mono font-semibold text-charcoal">
                  {bestScenario.delta_cumulative_exposure_pct}%
                </span>
                <span className="text-xs text-charcoal-muted block">Avoided Burden</span>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Comparison Chart */}
      <div className="rounded-xl border border-[#E5E5DF] bg-white p-6 shadow-[0_1px_3px_rgba(0,0,0,0.02)]">
        <div className="flex flex-wrap items-center justify-between gap-4 border-b border-[#F2F2EC] pb-4 mb-4">
          <div>
            <h3 className="text-sm font-semibold tracking-tight text-charcoal">
              Cross-Scenario Benchmark (72-Hour Horizon)
            </h3>
            <p className="text-xs text-charcoal-muted">
              Comparative impact on acute peak concentrations versus sustained cumulative exposure
            </p>
          </div>

          <div className="flex items-center gap-1 rounded-md border border-[#E5E5DF] bg-[#FAFAF7] p-1 text-xs">
            <button
              onClick={() => setMetricView('peak')}
              className={`rounded px-3 py-1 text-xs font-medium transition-colors ${
                metricView === 'peak'
                  ? 'bg-white text-charcoal font-semibold shadow-[0_1px_2px_rgba(0,0,0,0.04)] border border-[#E5E5DF]'
                  : 'text-charcoal-muted hover:text-charcoal'
              }`}
            >
              Peak PM2.5 (µg/m³)
            </button>
            <button
              onClick={() => setMetricView('exposure')}
              className={`rounded px-3 py-1 text-xs font-medium transition-colors ${
                metricView === 'exposure'
                  ? 'bg-white text-charcoal font-semibold shadow-[0_1px_2px_rgba(0,0,0,0.04)] border border-[#E5E5DF]'
                  : 'text-charcoal-muted hover:text-charcoal'
              }`}
            >
              Cumulative Burden (µg·h/m³)
            </button>
          </div>
        </div>

        <div className="h-80 w-full">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart
              data={chartData}
              layout="vertical"
              margin={{ top: 10, right: 30, left: 160, bottom: 5 }}
            >
              <CartesianGrid strokeDasharray="3 3" stroke="#F0F0EB" horizontal={false} />
              <XAxis type="number" stroke="#8C959D" fontSize={11} tickLine={false} />
              <YAxis
                type="category"
                dataKey="name"
                stroke="#5A626A"
                fontSize={11}
                tickLine={false}
                width={150}
              />
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
              <Bar
                dataKey={metricView === 'peak' ? 'peak' : 'exposure'}
                radius={[0, 4, 4, 0]}
                name={metricView === 'peak' ? 'Peak PM2.5 (µg/m³)' : 'Cumulative Exposure (µg·h/m³)'}
              >
                {chartData.map((entry, index) => (
                  <Cell
                    key={`cell-${index}`}
                    fill={
                      entry.isReduction
                        ? entry.delta_pct < -30
                          ? '#527D75'
                          : '#7899B5'
                        : entry.delta_pct === 0
                        ? '#8C959D'
                        : '#C26738'
                    }
                  />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Comprehensive Scenario Matrix Table */}
      <div className="rounded-xl border border-[#E5E5DF] bg-white overflow-hidden shadow-[0_1px_3px_rgba(0,0,0,0.02)]">
        <div className="p-5 border-b border-[#F2F2EC]">
          <h3 className="text-sm font-semibold tracking-tight text-charcoal">
            Full Policy Scenario Comparison Matrix
          </h3>
          <p className="text-xs text-charcoal-muted">
            All indicators computed via 2D physical transport simulation and counterfactual emission modeling
          </p>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-[#FAF8F5] text-[11px] font-medium text-charcoal-muted uppercase tracking-wider border-b border-[#E5E5DF]">
              <tr>
                <th className="py-3 px-4 font-medium">Scenario</th>
                <th className="py-3 px-4 font-medium">Peak PM2.5</th>
                <th className="py-3 px-4 font-medium">Δ vs. Baseline</th>
                <th className="py-3 px-4 font-medium">Time to Peak</th>
                <th className="py-3 px-4 font-medium">Cumulative Burden</th>
                <th className="py-3 px-4 font-medium">Δ Exposure (%)</th>
                <th className="py-3 px-4 font-medium">NAAQS Exceedance</th>
                <th className="py-3 px-4 text-right font-medium">Exposure Index</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[#F2F2EC] font-sans">
              {table.map((row) => {
                const isRed = row.delta_peak_pm25 <= 0;
                return (
                  <tr key={row.scenario_type} className="hover:bg-[#FAF8F5] transition-colors">
                    <td className="py-3 px-4">
                      <div className="font-medium text-charcoal">{row.scenario_name}</div>
                      <div className="font-mono text-[10px] text-charcoal-muted">{row.scenario_type}</div>
                    </td>
                    <td className="py-3 px-4 font-mono font-semibold text-charcoal">
                      {row.peak_pm25.toFixed(1)} µg/m³
                    </td>
                    <td className="py-3 px-4 font-mono">
                      <span
                        className={`inline-flex items-center gap-1 font-semibold ${
                          isRed
                            ? row.delta_peak_pm25 === 0
                              ? 'text-charcoal-muted'
                              : 'text-[#3D8B7A]'
                            : 'text-[#C26738]'
                        }`}
                      >
                        {row.delta_peak_pm25 > 0 ? '+' : ''}
                        {row.delta_peak_pm25.toFixed(1)} ({row.delta_peak_pct > 0 ? '+' : ''}
                        {row.delta_peak_pct}%)
                      </span>
                    </td>
                    <td className="py-3 px-4 font-mono text-charcoal-muted">
                      +{row.time_to_peak_hours}h ({row.peak_shift_hours >= 0 ? '+' : ''}
                      {row.peak_shift_hours}h shift)
                    </td>
                    <td className="py-3 px-4 font-mono text-charcoal">
                      {row.cumulative_exposure_pm25.toFixed(0)} µg·h/m³
                    </td>
                    <td className="py-3 px-4 font-mono">
                      <span
                        className={`font-semibold ${
                          row.delta_cumulative_exposure_pct <= 0
                            ? row.delta_cumulative_exposure_pct === 0
                              ? 'text-charcoal-muted'
                              : 'text-[#3D8B7A]'
                            : 'text-[#C26738]'
                        }`}
                      >
                        {row.delta_cumulative_exposure_pct > 0 ? '+' : ''}
                        {row.delta_cumulative_exposure_pct}%
                      </span>
                    </td>
                    <td className="py-3 px-4 font-mono text-charcoal-muted">
                      {row.exceedance_hours_pm25_60} hours
                    </td>
                    <td className="py-3 px-4 text-right font-mono font-semibold text-brand-green">
                      {row.population_weighted_exposure_index.toFixed(1)}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
