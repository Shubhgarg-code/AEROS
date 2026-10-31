import React, { useState, useEffect } from 'react';
import {
  Cpu,
  ShieldCheck,
  CheckCircle2,
  AlertTriangle,
  Layers,
  Database,
  Activity,
  GitBranch,
  Terminal,
} from 'lucide-react';
import { apiClient } from '../api/client';
import { HealthData, ModelMetadata } from '../types';
import { MetricCard } from '../components/MetricCard';

export const ModelIntelligencePage: React.FC = () => {
  const [metadata, setMetadata] = useState<ModelMetadata | null>(null);
  const [health, setHealth] = useState<HealthData | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchMetadata = async () => {
      try {
        setLoading(true);
        const [metaRes, healthRes] = await Promise.all([
          apiClient.getModelsMetadata(),
          apiClient.getSimulationHealth(),
        ]);
        setMetadata(metaRes);
        setHealth(healthRes);
      } catch (err: any) {
        setError(err.message || 'Failed to fetch model metadata.');
      } finally {
        setLoading(false);
      }
    };
    fetchMetadata();
  }, []);

  return (
    <div className="space-y-6">
      {/* System Integrity Headline */}
      <div className="rounded-xl border border-[#E5E5DF] bg-white p-6 shadow-[0_1px_3px_rgba(0,0,0,0.02)]">
        <div className="flex flex-wrap items-center justify-between gap-4 border-b border-[#F2F2EC] pb-4">
          <div>
            <div className="flex items-center gap-2">
              <ShieldCheck className="h-4 w-4 text-brand-green" />
              <h3 className="text-sm font-semibold tracking-tight text-charcoal">
                Model Intelligence & Validation Standards
              </h3>
            </div>
            <p className="text-xs text-charcoal-muted mt-1">
              Empirical audit metrics, holdout test benchmarks, and documented scientific boundaries
            </p>
          </div>

          <div className="flex items-center gap-3 text-xs">
            <span className="flex items-center gap-1.5 rounded-full border border-[#CDE5DF] bg-[#EAF4F1] px-3 py-1 font-medium text-[#285D52]">
              <span className="h-1.5 w-1.5 rounded-full bg-[#3D8B7A]" />
              System Healthy
            </span>
            <span className="text-[#C5C5BD]">•</span>
            <span className="text-charcoal-muted font-mono text-[11px]">v1.7.0</span>
          </div>
        </div>

        {/* System Overview KPI Cards */}
        <div className="mt-5 grid grid-cols-1 gap-4 sm:grid-cols-4">
          <MetricCard
            title="Training Observations"
            value="39,600"
            unit="records"
            subtitle="5 Diwali windows (2021–2025)"
            trend={{ value: 'Zero Data Leakage', isPositive: true }}
          />

          <MetricCard
            title="Spatial Grid Resolution"
            value="121"
            unit="cells"
            subtitle="0.05° (~5.5 km) mesh"
            trend={{ value: 'Delhi NCR Airshed', isNeutral: true }}
          />

          <MetricCard
            title="Forecasting Horizons"
            value="7"
            unit="horizons"
            subtitle="1h, 3h, 6h, 12h, 24h, 48h, 72h"
            trend={{ value: 'Multi-Horizon Models', isNeutral: true }}
          />

          <MetricCard
            title="Spatial Holdout Monitors"
            value="3"
            unit="stations"
            subtitle="Dwarka, Jahangirpuri, Mandir Marg"
            trend={{ value: 'Unseen Validation', isPositive: true }}
          />
        </div>
      </div>

      {/* Model Family Performance Comparison Tables */}
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        {/* Table 1: Temporal Models */}
        <div className="rounded-xl border border-[#E5E5DF] bg-white overflow-hidden shadow-[0_1px_3px_rgba(0,0,0,0.02)]">
          <div className="p-5 border-b border-[#F2F2EC]">
            <div className="flex items-center justify-between">
              <h4 className="text-xs font-semibold uppercase tracking-wider text-charcoal">
                Temporal Forecaster Benchmarks (24h Horizon)
              </h4>
              <span className="rounded bg-[#EEF4F8] px-2 py-0.5 text-[10px] font-mono text-[#50728F] border border-[#D5E3EC]">
                Held-Out 2025 Test Set
              </span>
            </div>
            <p className="text-xs text-charcoal-muted mt-1">
              Evaluated strictly on chronological post-split test observations
            </p>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-[#FAF8F5] text-[11px] font-medium text-charcoal-muted uppercase tracking-wider border-b border-[#E5E5DF]">
                <tr>
                  <th className="py-2.5 px-4 font-medium">Architecture</th>
                  <th className="py-2.5 px-4 font-medium">PM2.5 MAE</th>
                  <th className="py-2.5 px-4 font-medium">PM2.5 RMSE</th>
                  <th className="py-2.5 px-4 text-right font-medium">Holdout R²</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[#F2F2EC] font-sans">
                {metadata?.temporal_models.map((m, idx) => (
                  <tr key={idx} className="hover:bg-[#FAF8F5] transition-colors">
                    <td className="py-2.5 px-4 font-medium text-charcoal">
                      {m.model}
                    </td>
                    <td className="py-2.5 px-4 font-mono font-semibold text-brand-green">{m.pm25_mae.toFixed(2)} µg/m³</td>
                    <td className="py-2.5 px-4 font-mono text-charcoal-muted">{m.pm25_rmse.toFixed(2)}</td>
                    <td className="py-2.5 px-4 text-right font-mono font-semibold text-charcoal">
                      {m.pm25_r2.toFixed(3)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        {/* Table 2: Spatial Graph Models */}
        <div className="rounded-xl border border-[#E5E5DF] bg-white overflow-hidden shadow-[0_1px_3px_rgba(0,0,0,0.02)]">
          <div className="p-5 border-b border-[#F2F2EC]">
            <div className="flex items-center justify-between">
              <h4 className="text-xs font-semibold uppercase tracking-wider text-charcoal">
                Spatial Architecture Holdout Benchmarks
              </h4>
              <span className="rounded bg-[#EAF4F1] px-2 py-0.5 text-[10px] font-mono text-[#285D52] border border-[#CDE5DF]">
                Unseen Physical Stations
              </span>
            </div>
            <p className="text-xs text-charcoal-muted mt-1">
              Evaluated strictly on unseen physical stations (Dwarka, Jahangirpuri, Mandir Marg)
            </p>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-[#FAF8F5] text-[11px] font-medium text-charcoal-muted uppercase tracking-wider border-b border-[#E5E5DF]">
                <tr>
                  <th className="py-2.5 px-4 font-medium">Spatial Architecture</th>
                  <th className="py-2.5 px-4 font-medium">PM2.5 MAE</th>
                  <th className="py-2.5 px-4 font-medium">PM2.5 RMSE</th>
                  <th className="py-2.5 px-4 text-right font-medium">Holdout R²</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[#F2F2EC] font-sans">
                {metadata?.spatial_models.map((m, idx) => (
                  <tr key={idx} className="hover:bg-[#FAF8F5] transition-colors">
                    <td className="py-2.5 px-4 font-medium text-charcoal">
                      {m.model}
                    </td>
                    <td className="py-2.5 px-4 font-mono font-semibold text-brand-green">{m.pm25_mae.toFixed(2)} µg/m³</td>
                    <td className="py-2.5 px-4 font-mono text-charcoal-muted">{m.pm25_rmse.toFixed(2)}</td>
                    <td className="py-2.5 px-4 text-right font-mono font-semibold text-charcoal">
                      {m.pm25_r2.toFixed(3)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>

      {/* Numerical Solvers & Physics Architecture Specs */}
      {health && (
        <div className="rounded-xl border border-[#E5E5DF] bg-white p-6 shadow-[0_1px_3px_rgba(0,0,0,0.02)]">
          <h4 className="text-xs font-semibold uppercase tracking-wider text-charcoal mb-4">
            Atmospheric Fluid Transport & Numerical Solver Specifications
          </h4>

          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3 text-xs">
            <div className="rounded-lg border border-[#E5E5DF] bg-[#FAFAF7] p-4 space-y-1">
              <span className="text-[10px] text-charcoal-muted block uppercase font-medium">Advective Numerical Scheme</span>
              <span className="text-charcoal font-semibold font-mono text-xs">{health.physics_solver.advection_scheme}</span>
              <p className="text-xs text-charcoal-muted pt-1 leading-relaxed">
                Prevents non-physical oscillations in steep spatial pollution gradients.
              </p>
            </div>

            <div className="rounded-lg border border-[#E5E5DF] bg-[#FAFAF7] p-4 space-y-1">
              <span className="text-[10px] text-charcoal-muted block uppercase font-medium">Turbulent Diffusion Scheme</span>
              <span className="text-charcoal font-semibold font-mono text-xs">{health.physics_solver.diffusion_scheme}</span>
              <p className="text-xs text-charcoal-muted pt-1 leading-relaxed">
                Eddy diffusivity K ≈ 8.0 km²/h calibrated against post-monsoon horizontal turbulence.
              </p>
            </div>

            <div className="rounded-lg border border-[#E5E5DF] bg-[#FAFAF7] p-4 space-y-1">
              <span className="text-[10px] text-charcoal-muted block uppercase font-medium">Time Integration & Stability</span>
              <span className="text-charcoal font-semibold font-mono text-xs">{health.physics_solver.time_integration}</span>
              <p className="text-xs text-charcoal-muted pt-1 leading-relaxed">
                CFL ≤ 1.0 explicitly enforced via dynamic internal sub-stepping (δt ≈ 0.05h).
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Known Limitations and Scientific Transparency */}
      <div className="rounded-xl border border-[#E5E5DF] bg-white p-6 shadow-[0_1px_3px_rgba(0,0,0,0.02)]">
        <div className="flex items-center gap-2 mb-3">
          <AlertTriangle className="h-4 w-4 text-[#C48A2C]" />
          <h4 className="text-xs font-semibold uppercase tracking-wider text-charcoal">
            Documented Scientific Boundaries & Limitations
          </h4>
        </div>

        <ul className="space-y-2 text-xs text-charcoal-muted list-disc list-inside leading-relaxed">
          {metadata?.known_limitations.map((lim, i) => (
            <li key={i}>{lim}</li>
          ))}
          <li>
            Precipitation scavenging is modeled empirically; intense localized convective cloud bursts may clear particulate faster than linear scavenging rates.
          </li>
          <li>
            Agricultural crop residue burning (stubble burning) in Punjab and Haryana is captured through regional reanalysis inflows at the northwesterly boundary rather than direct farm-level emission inventories.
          </li>
        </ul>
      </div>
    </div>
  );
};
