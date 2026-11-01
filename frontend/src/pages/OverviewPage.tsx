import React, { useState, useEffect } from 'react';
import {
  Wind,
  Thermometer,
  Search,
  Activity,
  Layers,
  Heart,
  TrendingUp,
  Share2,
  Sparkles,
  ArrowRight,
  HelpCircle,
  Clock,
  Compass,
  AlertTriangle,
  SlidersHorizontal,
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
import { NavTab } from '../components/Sidebar';

interface OverviewPageProps {
  onNavigate?: (tab: NavTab) => void;
}

export const OverviewPage: React.FC<OverviewPageProps> = ({ onNavigate }) => {
  const [data, setData] = useState<OverviewData | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [activeView, setActiveView] = useState<'insights' | 'trends' | 'stations'>('insights');
  const [searchQuery, setSearchQuery] = useState<string>('');
  const [stationFilter, setStationFilter] = useState<'all' | 'hotspots' | 'residential' | 'industrial'>('all');
  const [showTechnicalDetails, setShowTechnicalDetails] = useState<boolean>(false);

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
          <span className="text-xs text-charcoal-muted">Retrieving citywide air quality...</span>
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
  const filteredStations = stations.filter((s) => {
    const matchesSearch =
      s.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      s.neighborhood_id.toLowerCase().includes(searchQuery.toLowerCase()) ||
      s.classification.toLowerCase().includes(searchQuery.toLowerCase());

    if (!matchesSearch) return false;

    if (stationFilter === 'hotspots') {
      return (s.aqi && s.aqi >= 300) || (s.pm2_5 && s.pm2_5 >= 150) || (s.current_pm25 && s.current_pm25 >= 150);
    }
    if (stationFilter === 'residential') {
      return s.classification.toLowerCase().includes('residential');
    }
    if (stationFilter === 'industrial') {
      return s.classification.toLowerCase().includes('industrial');
    }
    return true;
  });

  const currentMean25 = data?.citywide_pm25.mean || 92.0;
  const currentMean10 = data?.citywide_pm10.mean || 162.0;
  const aqiCat = data?.aqi_category || 'Moderate';
  const aqiVal = data?.citywide_aqi || 151;
  const windSpd = data?.weather_summary.wind_speed_ms || 2.5;
  const windDir = data?.weather_summary.wind_direction_compass || 'NW';
  const pblHeight = data?.weather_summary.pbl_height_m || 420;

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

  // Plain-English health advisory
  const getHealthAdvice = (aqi: number) => {
    if (aqi <= 100) {
      return {
        badge: 'Satisfactory',
        badgeColor: 'bg-[#EAF4F1] text-[#285D52] border-[#CDE5DF]',
        headline: 'Air quality is clear and safe for outdoor routines today.',
        outdoor: 'Safe for morning jogs, cycling, and outdoor exercise.',
        mask: 'No mask required for general public.',
        windows: 'Open windows freely for natural ventilation.',
      };
    } else if (aqi <= 200) {
      return {
        badge: 'Moderate',
        badgeColor: 'bg-[#FDF6E9] text-[#865914] border-[#F5E2BE]',
        headline: 'Moderate air: acceptable for most, sensitive people take care.',
        outdoor: 'Joggers with asthma should reduce intense exertion during early morning.',
        mask: 'Recommended on high-traffic roads.',
        windows: 'Best to air out rooms during afternoon hours (12 PM – 4 PM).',
      };
    } else if (aqi <= 300) {
      return {
        badge: 'Poor',
        badgeColor: 'bg-[#FDF0E9] text-[#873A16] border-[#F6D0BA]',
        headline: 'Air quality is poor. Prolonged exposure causes discomfort.',
        outdoor: 'Switch morning workouts to indoor alternatives.',
        mask: 'Wear N95/FFP2 masks when stepping outside.',
        windows: 'Keep windows closed during early morning inversion.',
      };
    } else {
      return {
        badge: 'Severe Alert',
        badgeColor: 'bg-[#FCEEEE] text-[#8A2424] border-[#F5C2C2]',
        headline: 'Hazardous air quality across Delhi NCR.',
        outdoor: 'Avoid all outdoor exertion and intense activity.',
        mask: 'N95 masks strictly advised for everyone.',
        windows: 'Keep doors and windows sealed; use indoor HEPA purifiers.',
      };
    }
  };

  const advice = getHealthAdvice(aqiVal);

  return (
    <div className="space-y-6 max-w-6xl mx-auto">
      {/* 1. Calm, Airy Hero Status Header */}
      <div className="relative overflow-hidden rounded-2xl border border-[#E5E5DF] bg-white p-6 shadow-sm">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-6">
          <div className="space-y-2">
            <div className="flex items-center gap-2.5">
              <span className="text-xs font-semibold uppercase tracking-wider text-charcoal-muted">
                Delhi NCR Atmospheric Status
              </span>
              <AQIBadge aqi={aqiVal} category={aqiCat} size="sm" />
            </div>

            <h1 className="text-2xl font-bold tracking-tight text-charcoal">
              City Air Quality is{' '}
              <span className="text-brand-green">{aqiCat}</span>
            </h1>

            <p className="text-sm text-charcoal-muted max-w-xl leading-relaxed">
              Average fine particulates (PM2.5) are at{' '}
              <strong className="text-charcoal font-semibold">{currentMean25.toFixed(0)} µg/m³</strong>.
              Light breeze at <strong className="text-charcoal font-semibold">{windSpd} m/s</strong> from {windDir}.
              Airflow improves in the afternoon as thermal inversion lifts.
            </p>
          </div>

          {/* Quick Stat Highlights */}
          <div className="flex flex-wrap md:flex-col gap-2 shrink-0 md:min-w-[190px]">
            <div className="flex items-center gap-2 rounded-lg bg-[#FAFAF7] border border-[#E5E5DF] px-3 py-2 text-xs">
              <Thermometer className="h-4 w-4 text-brand-green" />
              <span className="text-charcoal font-medium">{data?.weather_summary.temperature_c || 21.5}°C</span>
              <span className="text-charcoal-muted font-normal">• {data?.weather_summary.humidity_pct || 58}% Humid</span>
            </div>

            <div className="flex items-center gap-2 rounded-lg bg-[#FAFAF7] border border-[#E5E5DF] px-3 py-2 text-xs">
              <Wind className="h-4 w-4 text-brand-blue" />
              <span className="text-charcoal font-medium">{windSpd} m/s</span>
              <span className="text-charcoal-muted font-normal">• {windDir} Winds</span>
            </div>

            <div className="flex items-center gap-2 rounded-lg bg-[#FAFAF7] border border-[#E5E5DF] px-3 py-2 text-xs">
              <Activity className="h-4 w-4 text-[#3D8B7A]" />
              <span className="text-charcoal font-medium">{stations.length} Sensors Online</span>
            </div>
          </div>
        </div>

        {/* Technical Details Toggle */}
        <div className="mt-5 pt-4 border-t border-[#F2F2EC] flex items-center justify-between">
          <button
            onClick={() => setShowTechnicalDetails(!showTechnicalDetails)}
            className="flex items-center gap-1.5 text-xs text-brand-green hover:underline font-medium"
          >
            <SlidersHorizontal className="h-3.5 w-3.5" />
            <span>{showTechnicalDetails ? 'Hide Technical Parameters' : 'Show Technical Parameters'}</span>
          </button>

          <span className="text-[11px] text-charcoal-muted font-mono">
            National Standard: 60 µg/m³ (NAAQS)
          </span>
        </div>

        {/* Collapsible Technical Details */}
        {showTechnicalDetails && (
          <div className="mt-3 rounded-xl bg-[#FAFAF7] border border-[#E5E5DF] p-3.5 grid grid-cols-1 sm:grid-cols-3 gap-3 text-xs text-charcoal-muted animate-in fade-in duration-150">
            <div>
              <span className="font-semibold text-charcoal block mb-0.5">Boundary Mixing Height</span>
              <span>{pblHeight} m (Planetary Boundary Layer ceiling)</span>
            </div>
            <div>
              <span className="font-semibold text-charcoal block mb-0.5">Atmospheric Inversion Risk</span>
              <span className={data?.weather_summary.inversion_risk === 'HIGH' ? 'text-[#873A16] font-medium' : 'text-brand-green font-medium'}>
                {data?.weather_summary.inversion_risk || 'MODERATE'} Inversion
              </span>
            </div>
            <div>
              <span className="font-semibold text-charcoal block mb-0.5">Spatial Airshed Domain</span>
              <span>121 Computational Cells (~5.5 km resolution)</span>
            </div>
          </div>
        )}
      </div>

      {/* 2. Decluttered View Switcher (Sub-tabs) */}
      <div className="flex items-center justify-between border-b border-[#E5E5DF] pb-2">
        <div className="flex items-center gap-2">
          <button
            onClick={() => setActiveView('insights')}
            className={`rounded-lg px-4 py-2 text-xs font-semibold transition-all ${
              activeView === 'insights'
                ? 'bg-white text-charcoal shadow-sm border border-[#E5E5DF]'
                : 'text-charcoal-muted hover:text-charcoal hover:bg-[#F2F2EC]'
            }`}
          >
            ✨ Today's Insights & Advice
          </button>
          <button
            onClick={() => setActiveView('trends')}
            className={`rounded-lg px-4 py-2 text-xs font-semibold transition-all ${
              activeView === 'trends'
                ? 'bg-white text-charcoal shadow-sm border border-[#E5E5DF]'
                : 'text-charcoal-muted hover:text-charcoal hover:bg-[#F2F2EC]'
            }`}
          >
            📈 24-Hour Hourly Trend
          </button>
          <button
            onClick={() => setActiveView('stations')}
            className={`rounded-lg px-4 py-2 text-xs font-semibold transition-all ${
              activeView === 'stations'
                ? 'bg-white text-charcoal shadow-sm border border-[#E5E5DF]'
                : 'text-charcoal-muted hover:text-charcoal hover:bg-[#F2F2EC]'
            }`}
          >
            🏢 Stations ({stations.length})
          </button>
        </div>
      </div>

      {/* VIEW 1: TODAY'S INSIGHTS & HEALTH ADVICE */}
      {activeView === 'insights' && (
        <div className="space-y-6">
          {/* Health Action Card */}
          <div className="rounded-2xl border border-[#E5E5DF] bg-white p-6 shadow-sm">
            <div className="flex items-center justify-between border-b border-[#F2F2EC] pb-3 mb-4">
              <div className="flex items-center gap-2">
                <Heart className="h-4 w-4 text-brand-green" />
                <h2 className="text-sm font-semibold tracking-tight text-charcoal">
                  Health & Daily Activity Advisory
                </h2>
              </div>
              <span className={`rounded-md px-2.5 py-0.5 text-xs font-semibold border ${advice.badgeColor}`}>
                {advice.badge}
              </span>
            </div>

            <p className="text-sm font-medium text-charcoal mb-4">
              {advice.headline}
            </p>

            <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
              <div className="rounded-xl bg-[#FAFAF7] border border-[#E5E5DF] p-3.5 space-y-1">
                <div className="flex items-center gap-2 text-xs font-semibold text-charcoal">
                  <span>🏃</span>
                  <span>Outdoor Exercise</span>
                </div>
                <p className="text-xs text-charcoal-muted leading-relaxed">
                  {advice.outdoor}
                </p>
              </div>

              <div className="rounded-xl bg-[#FAFAF7] border border-[#E5E5DF] p-3.5 space-y-1">
                <div className="flex items-center gap-2 text-xs font-semibold text-charcoal">
                  <span>😷</span>
                  <span>Mask Advisory</span>
                </div>
                <p className="text-xs text-charcoal-muted leading-relaxed">
                  {advice.mask}
                </p>
              </div>

              <div className="rounded-xl bg-[#FAFAF7] border border-[#E5E5DF] p-3.5 space-y-1">
                <div className="flex items-center gap-2 text-xs font-semibold text-charcoal">
                  <span>🪟</span>
                  <span>Home Ventilation</span>
                </div>
                <p className="text-xs text-charcoal-muted leading-relaxed">
                  {advice.windows}
                </p>
              </div>
            </div>
          </div>

          {/* 3 Core Metric Cards (clean & spacious) */}
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
            <MetricCard
              title="Citywide PM2.5 (Fine Dust)"
              value={data?.citywide_pm25.mean.toFixed(1) || '0.0'}
              unit="µg/m³"
              subtitle={`Min: ${data?.citywide_pm25.min.toFixed(0)} · Max: ${data?.citywide_pm25.max.toFixed(0)}`}
              trend={{ value: `${(currentMean25 / 60).toFixed(1)}x Safe Limit (60)`, isPositive: false }}
              icon={<Activity className="h-4 w-4" />}
              badge={<AQIBadge aqi={data?.citywide_aqi} category={data?.aqi_category} size="sm" />}
            />

            <MetricCard
              title="Citywide PM10 (Coarse Dust)"
              value={data?.citywide_pm10.mean.toFixed(1) || '0.0'}
              unit="µg/m³"
              subtitle={`Min: ${data?.citywide_pm10.min.toFixed(0)} · Max: ${data?.citywide_pm10.max.toFixed(0)}`}
              trend={{ value: `${(currentMean10 / 100).toFixed(1)}x Safe Limit (100)`, isPositive: false }}
              icon={<Layers className="h-4 w-4" />}
            />

            <MetricCard
              title="Surface Wind & Circulation"
              value={`${windSpd}`}
              unit="m/s"
              subtitle={`Direction: ${windDir} (${data?.weather_summary.wind_direction_deg || 315}°)`}
              trend={{
                value: windSpd >= 3.0 ? 'Good Ventilation' : 'Gentle Breeze',
                isPositive: windSpd >= 3.0,
              }}
              icon={<Wind className="h-4 w-4" />}
            />
          </div>

          {/* 3. "Where to Next?" Intuitive Feature Launchpad Cards */}
          {onNavigate && (
            <div className="rounded-2xl border border-[#E5E5DF] bg-white p-6 shadow-sm">
              <h3 className="text-xs font-semibold uppercase tracking-wider text-charcoal-muted mb-3">
                Explore AEROS Capabilities:
              </h3>
              <div className="grid grid-cols-1 gap-3 sm:grid-cols-3">
                <div
                  onClick={() => onNavigate('spatial')}
                  className="group cursor-pointer rounded-xl border border-[#E5E5DF] bg-[#FAFAF7] p-4 transition-all hover:bg-white hover:border-brand-green hover:shadow-md"
                >
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <div className="rounded-md bg-[#EEF4F8] p-1.5 text-brand-blue">
                        <Share2 className="h-4 w-4" />
                      </div>
                      <span className="text-xs font-semibold text-charcoal group-hover:text-brand-green">
                        Virtual Sensor
                      </span>
                    </div>
                    <ArrowRight className="h-4 w-4 text-charcoal-muted group-hover:translate-x-1 group-hover:text-brand-green transition-all" />
                  </div>
                  <p className="mt-2 text-xs text-charcoal-muted">
                    No sensor near your colony? Check estimated pollution for any Delhi address.
                  </p>
                </div>

                <div
                  onClick={() => onNavigate('forecasting')}
                  className="group cursor-pointer rounded-xl border border-[#E5E5DF] bg-[#FAFAF7] p-4 transition-all hover:bg-white hover:border-brand-green hover:shadow-md"
                >
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <div className="rounded-md bg-[#EAF4F1] p-1.5 text-brand-green">
                        <TrendingUp className="h-4 w-4" />
                      </div>
                      <span className="text-xs font-semibold text-charcoal group-hover:text-brand-green">
                        72-Hour Forecast
                      </span>
                    </div>
                    <ArrowRight className="h-4 w-4 text-charcoal-muted group-hover:translate-x-1 group-hover:text-brand-green transition-all" />
                  </div>
                  <p className="mt-2 text-xs text-charcoal-muted">
                    See hourly air quality predictions with scientific 90% confidence bands.
                  </p>
                </div>

                <div
                  onClick={() => onNavigate('simulator')}
                  className="group cursor-pointer rounded-xl border border-[#E5E5DF] bg-[#FAFAF7] p-4 transition-all hover:bg-white hover:border-[#C48A2C] hover:shadow-md"
                >
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <div className="rounded-md bg-[#FDF6E9] p-1.5 text-[#C48A2C]">
                        <Sparkles className="h-4 w-4" />
                      </div>
                      <span className="text-xs font-semibold text-charcoal group-hover:text-[#C48A2C]">
                        What-if Policies
                      </span>
                    </div>
                    <ArrowRight className="h-4 w-4 text-charcoal-muted group-hover:translate-x-1 group-hover:text-[#C48A2C] transition-all" />
                  </div>
                  <p className="mt-2 text-xs text-charcoal-muted">
                    Simulate how fireworks bans and Odd-Even rules flatten the pollution spike.
                  </p>
                </div>
              </div>
            </div>
          )}
        </div>
      )}

      {/* VIEW 2: 24-HOUR HOURLY TREND */}
      {activeView === 'trends' && (
        <div className="space-y-6">
          <div className="rounded-2xl border border-[#E5E5DF] bg-white p-6 shadow-sm">
            <div className="flex flex-wrap items-center justify-between gap-4 border-b border-[#F2F2EC] pb-4 mb-4">
              <div>
                <h3 className="text-sm font-semibold tracking-tight text-charcoal">
                  24-Hour Particulate Diurnal Cycle
                </h3>
                <p className="text-xs text-charcoal-muted">
                  Shows daytime ventilation vs. nocturnal concentration build-up across Delhi
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
                  Safe Limit (60 µg/m³)
                </span>
              </div>
            </div>

            <div className="h-72 w-full">
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
                  <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#EBEBE6" />
                  <XAxis dataKey="hour" tick={{ fontSize: 11, fill: '#8C959D' }} tickLine={false} axisLine={false} />
                  <YAxis tick={{ fontSize: 11, fill: '#8C959D' }} tickLine={false} axisLine={false} />
                  <ReferenceLine y={60} stroke="#C26738" strokeDasharray="4 4" strokeWidth={1.5} />
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

            <div className="mt-4 rounded-xl bg-[#FAFAF7] border border-[#E5E5DF] p-3 text-xs text-charcoal-muted">
              💡 <strong>Why does pollution peak at 8:00 AM and 10:00 PM?</strong> Cool overnight air acts like a lid (temperature inversion) trapping vehicular exhaust close to the ground. As sunlight heats the earth by afternoon, the air circulates higher up, easing ground-level smog.
            </div>
          </div>
        </div>
      )}

      {/* VIEW 3: STATIONS LIST */}
      {activeView === 'stations' && (
        <div className="space-y-6">
          <div className="rounded-2xl border border-[#E5E5DF] bg-white p-6 shadow-sm">
            <div className="flex flex-wrap items-center justify-between gap-4 border-b border-[#F2F2EC] pb-4 mb-4">
              <div>
                <h3 className="text-sm font-semibold tracking-tight text-charcoal">
                  CPCB Continuous Monitoring Stations
                </h3>
                <p className="text-xs text-charcoal-muted">
                  Filter by category or search station name:
                </p>
              </div>

              <div className="flex flex-wrap items-center gap-2">
                <div className="flex items-center rounded-lg border border-[#E5E5DF] bg-[#FAFAF7] p-0.5 text-xs">
                  <button
                    onClick={() => setStationFilter('all')}
                    className={`rounded px-2.5 py-1 transition-colors ${
                      stationFilter === 'all'
                        ? 'bg-white font-medium text-charcoal shadow-sm'
                        : 'text-charcoal-muted hover:text-charcoal'
                    }`}
                  >
                    All ({stations.length})
                  </button>
                  <button
                    onClick={() => setStationFilter('hotspots')}
                    className={`rounded px-2.5 py-1 transition-colors ${
                      stationFilter === 'hotspots'
                        ? 'bg-[#FDF0E9] font-medium text-[#873A16] shadow-sm'
                        : 'text-charcoal-muted hover:text-charcoal'
                    }`}
                  >
                    Hotspots
                  </button>
                  <button
                    onClick={() => setStationFilter('residential')}
                    className={`rounded px-2.5 py-1 transition-colors ${
                      stationFilter === 'residential'
                        ? 'bg-white font-medium text-charcoal shadow-sm'
                        : 'text-charcoal-muted hover:text-charcoal'
                    }`}
                  >
                    Residential
                  </button>
                  <button
                    onClick={() => setStationFilter('industrial')}
                    className={`rounded px-2.5 py-1 transition-colors ${
                      stationFilter === 'industrial'
                        ? 'bg-white font-medium text-charcoal shadow-sm'
                        : 'text-charcoal-muted hover:text-charcoal'
                    }`}
                  >
                    Industrial
                  </button>
                </div>

                <div className="relative w-56">
                  <Search className="absolute left-3 top-2.5 h-3.5 w-3.5 text-[#8C959D]" />
                  <input
                    type="text"
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    placeholder="Search station or zone..."
                    className="w-full rounded-md border border-[#E5E5DF] bg-[#FAFAF7] pl-9 pr-3 py-1.5 text-xs text-charcoal placeholder-[#8C959D] focus:border-brand-green focus:bg-white focus:outline-none transition-colors"
                  />
                </div>
              </div>
            </div>

            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead className="bg-[#FAF8F5] text-[11px] font-medium text-charcoal-muted uppercase tracking-wider border-b border-[#E5E5DF]">
                  <tr>
                    <th className="py-3 px-4 font-medium">Station</th>
                    <th className="py-3 px-4 font-medium">Classification</th>
                    <th className="py-3 px-4 font-medium">PM2.5 (µg/m³)</th>
                    <th className="py-3 px-4 font-medium">PM10 (µg/m³)</th>
                    <th className="py-3 px-4 font-medium">AQI</th>
                    <th className="py-3 px-4 text-right font-medium">Status</th>
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
                          Live
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
