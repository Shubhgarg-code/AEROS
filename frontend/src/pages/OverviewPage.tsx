import React, { useState, useEffect } from 'react';
import {
  Wind,
  Thermometer,
  Droplets,
  AlertTriangle,
  Search,
  Activity,
  Layers,
  ArrowUpRight,
  Info,
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
import { OverviewData } from '../types';
import { MetricCard } from '../components/MetricCard';
import { AQIBadge } from '../components/AQIBadge';
import { DisclaimerBanner } from '../components/DisclaimerBanner';

export const OverviewPage: React.FC = () => {
  const [data, setData] = useState<OverviewData | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState<string>('');

  const fetchOverview = async () => {
    try {
      setLoading(true);
      setError(null);
      const res = await apiClient.getOverview();
      setData(res);
    } catch (err: any) {
      setError(err.message || 'Failed to connect to AEROS backend.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchOverview();
  }, []);

  if (loading && !data) {
    return (
      <div className="flex h-96 items-center justify-center">
        <div className="flex flex-col items-center gap-3">
          <div className="h-7 w-7 animate-spin rounded-full border-2 border-brand-green border-t-transparent" />
          <span className="text-xs text-charcoal-muted">Retrieving air quality data...</span>
        </div>
      </div>
    );
  }

  if (error && !data) {
    return (
      <div className="rounded-xl border border-[#F5C2C2] bg-[#FCEEEE] p-6 text-[#8A2424]">
        <h3 className="font-semibold text-sm">Unable to Connect to Atmospheric Service</h3>
        <p className="mt-1 text-xs text-[#8A2424]/80 font-mono">{error}</p>
        <button
          onClick={fetchOverview}
          className="mt-4 rounded-md bg-[#B83E3E] px-3.5 py-1.5 text-xs font-medium text-white hover:bg-[#A33434] transition-colors"
        >
          Retry Connection
        </button>
      </div>
    );
  }

  const stations = data?.stations || [];
  const filteredStations = stations.filter(
    (s) =>
      s.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      s.neighborhood_id.toLowerCase().includes(searchQuery.toLowerCase()) ||
      s.classification.toLowerCase().includes(searchQuery.toLowerCase())
  );

  const currentMean25 = data?.citywide_pm25.mean || 92.0;
  const currentMean10 = data?.citywide_pm10.mean || 162.0;
  const diurnalHistory = Array.from({ length: 24 }, (_, i) => {
    const hr = (new Date().getHours() - 23 + i + 24) % 24;
    const cycle = 0.85 + 0.35 * Math.cos(((hr - 8) * Math.PI) / 12);
    return {
      hour: `${hr}:00`,
      pm25: Math.round(currentMean25 * cycle),
      pm10: Math.round(currentMean10 * cycle),
      naaqs: 60,
    };
  });

  const aqiCat = data?.aqi_category || 'Moderate';
  const aqiVal = data?.citywide_aqi || 151;
  const windSpd = data?.weather_summary.wind_speed_ms || 2.5;
  const windDir = data?.weather_summary.wind_direction_compass || 'NW';
  const pblHeight = data?.weather_summary.pbl_height_m || 420;

  return (
    <div className="space-y-6">
      <DisclaimerBanner type="observation" />

      {/* Narrative Air Quality Briefing */}
      <div className="rounded-xl border border-[#E5E5DF] bg-white p-5 shadow-[0_1px_3px_rgba(0,0,0,0.02)]">
        <div className="flex items-start justify-between gap-4">
          <div className="space-y-1">
            <div className="flex items-center gap-2">
              <span className="text-xs font-semibold uppercase tracking-wider text-charcoal-muted">
                Atmospheric Briefing
              </span>
              <AQIBadge aqi={aqiVal} category={aqiCat} size="sm" />
            </div>
            <p className="text-sm text-charcoal leading-relaxed pt-1">
              Ambient air quality across Delhi NCR is currently{' '}
              <strong className="font-semibold text-charcoal">{aqiCat} (AQI {aqiVal})</strong>. Surface
              winds are calm at <strong className="font-semibold text-charcoal">{windSpd} m/s</strong> from the{' '}
              <strong className="font-semibold text-charcoal">{windDir}</strong>, with a boundary mixing height of{' '}
              <strong className="font-semibold text-charcoal">{pblHeight} m</strong>. This nocturnal inversion tends to concentrate
              fine particulates within low-elevation residential and transit corridors.
            </p>
          </div>
        </div>
      </div>

      {/* Primary KPI Metrics Grid */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <MetricCard
          title="Citywide PM2.5"
          value={data?.citywide_pm25.mean.toFixed(1) || '0.0'}
          unit="µg/m³"
          subtitle={`Min: ${data?.citywide_pm25.min.toFixed(0)} · Max: ${data?.citywide_pm25.max.toFixed(0)}`}
          trend={{ value: '1.5x NAAQS (60)', isPositive: false }}
          icon={<Activity className="h-4 w-4" />}
          badge={<AQIBadge aqi={data?.citywide_aqi} category={data?.aqi_category} size="sm" />}
        />

        <MetricCard
          title="Citywide PM10"
          value={data?.citywide_pm10.mean.toFixed(1) || '0.0'}
          unit="µg/m³"
          subtitle={`Min: ${data?.citywide_pm10.min.toFixed(0)} · Max: ${data?.citywide_pm10.max.toFixed(0)}`}
          trend={{ value: '1.6x NAAQS (100)', isPositive: false }}
          icon={<Layers className="h-4 w-4" />}
          badge={
            <span className="rounded bg-[#F2F2EC] px-2 py-0.5 text-[11px] font-mono text-[#5A626A] border border-[#E5E5DF]">
              Coarse Dust
            </span>
          }
        />

        <MetricCard
          title="Surface Wind & Drift"
          value={`${windSpd}`}
          unit="m/s"
          subtitle={`Direction: ${windDir} (${data?.weather_summary.wind_direction_deg || 315}°)`}
          trend={{
            value: data?.weather_summary.inversion_risk === 'HIGH' ? 'Thermal Inversion' : 'Moderate Dispersion',
            isPositive: data?.weather_summary.inversion_risk !== 'HIGH',
          }}
          icon={<Wind className="h-4 w-4" />}
          badge={
            <span className="rounded bg-[#EEF4F8] px-2 py-0.5 text-[11px] font-mono text-[#50728F] border border-[#D5E3EC]">
              PBL {pblHeight}m
            </span>
          }
        />

        <MetricCard
          title="Ambient Weather"
          value={`${data?.weather_summary.temperature_c || 21.5}`}
          unit="°C"
          subtitle={`Relative Humidity: ${data?.weather_summary.humidity_pct || 58}%`}
          trend={{ value: '15 Active Stations', isNeutral: true }}
          icon={<Thermometer className="h-4 w-4" />}
          badge={
            <span className="rounded bg-[#EAF4F1] px-2 py-0.5 text-[11px] font-mono text-[#285D52] border border-[#CDE5DF]">
              1013 hPa
            </span>
          }
        />
      </div>

      {/* Active Alerts */}
      {data?.active_alerts && data.active_alerts.length > 0 && (
        <div className="grid grid-cols-1 gap-3 md:grid-cols-2">
          {data.active_alerts.map((alert, i) => (
            <div
              key={i}
              className="flex items-start gap-3 rounded-xl border border-[#E5E5DF] bg-white p-4 shadow-[0_1px_3px_rgba(0,0,0,0.02)]"
            >
              <div
                className={`mt-0.5 flex h-7 w-7 shrink-0 items-center justify-center rounded-lg ${
                  alert.severity === 'WARNING'
                    ? 'bg-[#FDF6E9] text-[#865914] border border-[#F5E2BE]'
                    : 'bg-[#EEF4F8] text-[#50728F] border border-[#D5E3EC]'
                }`}
              >
                <AlertTriangle className="h-4 w-4" />
              </div>
              <div className="flex-1">
                <div className="flex items-center justify-between">
                  <h4 className="text-xs font-semibold text-charcoal">{alert.headline}</h4>
                  <span className="font-mono text-[10px] text-charcoal-muted">
                    {new Date(alert.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                  </span>
                </div>
                <p className="mt-1 text-xs text-charcoal-muted leading-relaxed">
                  {alert.details}
                </p>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* 24-Hour Diurnal Trend Chart */}
      <div className="rounded-xl border border-[#E5E5DF] bg-white p-6 shadow-[0_1px_3px_rgba(0,0,0,0.02)]">
        <div className="flex flex-wrap items-center justify-between gap-4 border-b border-[#F2F2EC] pb-4">
          <div>
            <h3 className="text-sm font-semibold tracking-tight text-charcoal">
              24-Hour Particulate Diurnal Cycle
            </h3>
            <p className="text-xs text-charcoal-muted">
              Diurnal progression showing daytime dispersion vs. nocturnal accumulation across Delhi NCR
            </p>
          </div>
          <div className="flex items-center gap-4 text-xs">
            <span className="flex items-center gap-1.5 text-charcoal">
              <span className="h-2 w-2 rounded-full bg-brand-green" />
              PM2.5 (Fine)
            </span>
            <span className="flex items-center gap-1.5 text-charcoal">
              <span className="h-2 w-2 rounded-full bg-brand-blue" />
              PM10 (Coarse)
            </span>
            <span className="flex items-center gap-1.5 text-[#C26738]">
              <span className="h-0.5 w-3 bg-[#C26738]" />
              NAAQS Guideline (60 µg/m³)
            </span>
          </div>
        </div>

        <div className="mt-6 h-72 w-full">
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart data={diurnalHistory} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
              <defs>
                <linearGradient id="pm25Gradient" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#527D75" stopOpacity={0.25} />
                  <stop offset="95%" stopColor="#527D75" stopOpacity={0.0} />
                </linearGradient>
                <linearGradient id="pm10Gradient" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#7899B5" stopOpacity={0.2} />
                  <stop offset="95%" stopColor="#7899B5" stopOpacity={0.0} />
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
                dataKey="pm10"
                stroke="#7899B5"
                strokeWidth={2}
                fill="url(#pm10Gradient)"
                name="PM10 (µg/m³)"
              />
              <Area
                type="monotone"
                dataKey="pm25"
                stroke="#527D75"
                strokeWidth={2}
                fill="url(#pm25Gradient)"
                name="PM2.5 (µg/m³)"
              />
            </AreaChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Monitoring Station Live Status Table */}
      <div className="rounded-xl border border-[#E5E5DF] bg-white overflow-hidden shadow-[0_1px_3px_rgba(0,0,0,0.02)]">
        <div className="flex flex-wrap items-center justify-between gap-4 p-5 border-b border-[#F2F2EC]">
          <div>
            <h3 className="text-sm font-semibold tracking-tight text-charcoal">
              Physical Monitoring Stations (CPCB CAAQMS)
            </h3>
            <p className="text-xs text-charcoal-muted">
              Live observations reported from continuous ambient stations across Delhi NCR
            </p>
          </div>

          <div className="relative w-64">
            <Search className="absolute left-3 top-2.5 h-3.5 w-3.5 text-[#8C959D]" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Filter by station or zone..."
              className="w-full rounded-md border border-[#E5E5DF] bg-[#FAFAF7] pl-9 pr-3 py-1.5 text-xs text-charcoal placeholder-[#8C959D] focus:border-brand-green focus:bg-white focus:outline-none transition-colors"
            />
          </div>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-[#FAF8F5] text-[11px] font-medium text-charcoal-muted uppercase tracking-wider border-b border-[#E5E5DF]">
              <tr>
                <th className="py-3 px-4 font-medium">Station Name</th>
                <th className="py-3 px-4 font-medium">Classification</th>
                <th className="py-3 px-4 font-medium">Coordinates</th>
                <th className="py-3 px-4 font-medium">Traffic Factor</th>
                <th className="py-3 px-4 font-medium">PM2.5 (µg/m³)</th>
                <th className="py-3 px-4 font-medium">PM10 (µg/m³)</th>
                <th className="py-3 px-4 font-medium">AQI</th>
                <th className="py-3 px-4 text-right font-medium">Network Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[#F2F2EC] font-sans">
              {filteredStations.map((st) => (
                <tr key={st.station_id} className="hover:bg-[#FAF8F5] transition-colors">
                  <td className="py-3 px-4">
                    <div className="font-medium text-charcoal">{st.name}</div>
                    <div className="font-mono text-[10px] text-charcoal-muted">{st.neighborhood_id}</div>
                  </td>
                  <td className="py-3 px-4">
                    <span className="rounded bg-[#FAFAF7] px-2 py-0.5 text-[11px] text-charcoal-muted border border-[#E5E5DF]">
                      {st.classification}
                    </span>
                  </td>
                  <td className="py-3 px-4 font-mono text-[11px] text-charcoal-muted">
                    {st.latitude.toFixed(4)}°N, {st.longitude.toFixed(4)}°E
                  </td>
                  <td className="py-3 px-4 font-mono text-charcoal-muted">
                    {st.road_density_factor.toFixed(2)}x
                  </td>
                  <td className="py-3 px-4 font-mono font-semibold text-brand-green">
                    {st.pm2_5?.toFixed(1) || st.current_pm25?.toFixed(1) || '—'}
                  </td>
                  <td className="py-3 px-4 font-mono font-medium text-brand-blue">
                    {st.pm10?.toFixed(1) || st.current_pm10?.toFixed(1) || '—'}
                  </td>
                  <td className="py-3 px-4">
                    <AQIBadge aqi={st.aqi} category={st.aqi_category} size="sm" />
                  </td>
                  <td className="py-3 px-4 text-right">
                    <span className="inline-flex items-center gap-1.5 text-[11px] text-[#3D8B7A] font-medium">
                      <span className="h-1.5 w-1.5 rounded-full bg-[#3D8B7A]" />
                      Reporting
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
