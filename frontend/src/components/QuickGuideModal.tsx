import React, { useState } from 'react';
import {
  X,
  BookOpen,
  MapPin,
  TrendingUp,
  Share2,
  Wind,
  Sparkles,
  Clock,
  BarChart3,
  CheckCircle2,
  ArrowRight,
  ShieldAlert,
  Heart,
  HelpCircle,
} from 'lucide-react';
import { NavTab } from './Sidebar';

interface QuickGuideModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSelectTab: (tab: NavTab) => void;
}

export const QuickGuideModal: React.FC<QuickGuideModalProps> = ({
  isOpen,
  onClose,
  onSelectTab,
}) => {
  const [activeGuideTab, setActiveGuideTab] = useState<'start' | 'features' | 'health' | 'faq'>('start');

  if (!isOpen) return null;

  const navigateTo = (tab: NavTab) => {
    onSelectTab(tab);
    onClose();
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4 backdrop-blur-sm animate-in fade-in duration-200">
      <div className="relative flex max-h-[90vh] w-full max-w-3xl flex-col rounded-2xl border border-[#E5E5DF] bg-white shadow-2xl">
        {/* Modal Header */}
        <div className="flex items-center justify-between border-b border-[#E5E5DF] px-6 py-4">
          <div className="flex items-center gap-2.5">
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-[#EAF4F1] text-brand-green border border-[#CDE5DF]">
              <BookOpen className="h-4 w-4" />
            </div>
            <div>
              <h2 className="text-base font-semibold tracking-tight text-charcoal">
                Welcome to AEROS Guide
              </h2>
              <p className="text-xs text-charcoal-muted">
                Your quick 2-minute walkthrough to understand and navigate the platform
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="rounded-lg p-1.5 text-charcoal-muted hover:bg-[#F2F2EC] hover:text-charcoal transition-colors"
            title="Close guide"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        {/* Guide Navigation Pills */}
        <div className="flex border-b border-[#F2F2EC] px-6 py-2.5 bg-[#FAFAF7] gap-2 overflow-x-auto">
          <button
            onClick={() => setActiveGuideTab('start')}
            className={`rounded-md px-3 py-1.5 text-xs font-medium transition-colors ${
              activeGuideTab === 'start'
                ? 'bg-white text-charcoal shadow-sm border border-[#E5E5DF]'
                : 'text-charcoal-muted hover:text-charcoal'
            }`}
          >
            🚀 Quick Start & Shortcuts
          </button>
          <button
            onClick={() => setActiveGuideTab('features')}
            className={`rounded-md px-3 py-1.5 text-xs font-medium transition-colors ${
              activeGuideTab === 'features'
                ? 'bg-white text-charcoal shadow-sm border border-[#E5E5DF]'
                : 'text-charcoal-muted hover:text-charcoal'
            }`}
          >
            🧭 What Does Each Page Do?
          </button>
          <button
            onClick={() => setActiveGuideTab('health')}
            className={`rounded-md px-3 py-1.5 text-xs font-medium transition-colors ${
              activeGuideTab === 'health'
                ? 'bg-white text-charcoal shadow-sm border border-[#E5E5DF]'
                : 'text-charcoal-muted hover:text-charcoal'
            }`}
          >
            ❤️ AQI & Health Guide
          </button>
          <button
            onClick={() => setActiveGuideTab('faq')}
            className={`rounded-md px-3 py-1.5 text-xs font-medium transition-colors ${
              activeGuideTab === 'faq'
                ? 'bg-white text-charcoal shadow-sm border border-[#E5E5DF]'
                : 'text-charcoal-muted hover:text-charcoal'
            }`}
          >
            ❓ Common Questions
          </button>
        </div>

        {/* Modal Scrollable Body */}
        <div className="flex-1 overflow-y-auto p-6 space-y-6">
          {/* TAB 1: QUICK START */}
          {activeGuideTab === 'start' && (
            <div className="space-y-6">
              <div className="rounded-xl border border-[#CDE5DF] bg-[#EAF4F1]/60 p-4">
                <h3 className="text-sm font-semibold text-[#285D52]">
                  What is AEROS in simple words?
                </h3>
                <p className="mt-1 text-xs text-[#285D52]/90 leading-relaxed">
                  Delhi NCR has over 30 million people but only 40 physical monitoring stations. 
                  AEROS is an <strong>Atmospheric Environmental Digital Twin</strong> that combines real-time sensor data, 
                  satellite readings, and physics-guided Graph Neural Networks to let you 
                  <strong> estimate pollution in unmonitored neighborhoods, forecast air quality up to 72 hours ahead, 
                  and simulate 'What-If' policy decisions.</strong>
                </p>
              </div>

              <div>
                <h4 className="text-xs font-semibold uppercase tracking-wider text-charcoal-muted mb-3">
                  Try Key Features in 1 Click:
                </h4>
                <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
                  <div
                    onClick={() => navigateTo('spatial')}
                    className="group cursor-pointer rounded-xl border border-[#E5E5DF] bg-white p-4 transition-all hover:border-brand-green hover:shadow-md"
                  >
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <div className="rounded-md bg-[#EEF4F8] p-2 text-brand-blue">
                          <Share2 className="h-4 w-4" />
                        </div>
                        <span className="text-xs font-semibold text-charcoal group-hover:text-brand-green">
                          Virtual Neighborhood Sensor
                        </span>
                      </div>
                      <ArrowRight className="h-4 w-4 text-charcoal-muted group-hover:translate-x-1 group-hover:text-brand-green transition-all" />
                    </div>
                    <p className="mt-2 text-[11px] text-charcoal-muted">
                      Check estimated pollution right at India Gate, Dwarka, or Saket where no direct sensor exists.
                    </p>
                  </div>

                  <div
                    onClick={() => navigateTo('simulator')}
                    className="group cursor-pointer rounded-xl border border-[#E5E5DF] bg-white p-4 transition-all hover:border-[#C48A2C] hover:shadow-md"
                  >
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <div className="rounded-md bg-[#FDF6E9] p-2 text-[#C48A2C]">
                          <Sparkles className="h-4 w-4" />
                        </div>
                        <span className="text-xs font-semibold text-charcoal group-hover:text-[#C48A2C]">
                          What-if Policy Sandbox
                        </span>
                      </div>
                      <ArrowRight className="h-4 w-4 text-charcoal-muted group-hover:translate-x-1 group-hover:text-[#C48A2C] transition-all" />
                    </div>
                    <p className="mt-2 text-[11px] text-charcoal-muted">
                      Test how fireworks curbs or Odd-Even traffic rules reduce PM2.5 spikes.
                    </p>
                  </div>

                  <div
                    onClick={() => navigateTo('forecasting')}
                    className="group cursor-pointer rounded-xl border border-[#E5E5DF] bg-white p-4 transition-all hover:border-brand-green hover:shadow-md"
                  >
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <div className="rounded-md bg-[#EAF4F1] p-2 text-brand-green">
                          <TrendingUp className="h-4 w-4" />
                        </div>
                        <span className="text-xs font-semibold text-charcoal group-hover:text-brand-green">
                          72-Hour AI Forecast
                        </span>
                      </div>
                      <ArrowRight className="h-4 w-4 text-charcoal-muted group-hover:translate-x-1 group-hover:text-brand-green transition-all" />
                    </div>
                    <p className="mt-2 text-[11px] text-charcoal-muted">
                      Inspect hourly future predictions with scientific 90% confidence bands.
                    </p>
                  </div>

                  <div
                    onClick={() => navigateTo('propagation')}
                    className="group cursor-pointer rounded-xl border border-[#E5E5DF] bg-white p-4 transition-all hover:border-brand-blue hover:shadow-md"
                  >
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <div className="rounded-md bg-[#EEF4F8] p-2 text-brand-blue">
                          <Wind className="h-4 w-4" />
                        </div>
                        <span className="text-xs font-semibold text-charcoal group-hover:text-brand-blue">
                          Smoke & Plume Drift
                        </span>
                      </div>
                      <ArrowRight className="h-4 w-4 text-charcoal-muted group-hover:translate-x-1 group-hover:text-brand-blue transition-all" />
                    </div>
                    <p className="mt-2 text-[11px] text-charcoal-muted">
                      Watch how factory plumes and stubble smoke travel downwind using physics simulations.
                    </p>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* TAB 2: PAGE BY PAGE */}
          {activeGuideTab === 'features' && (
            <div className="space-y-4">
              <div className="rounded-xl border border-[#E5E5DF] bg-white p-4">
                <div className="flex items-center gap-2 text-xs font-semibold text-charcoal">
                  <MapPin className="h-4 w-4 text-brand-green" />
                  <span>1. Overview & Environmental Map</span>
                </div>
                <p className="mt-1 text-xs text-charcoal-muted leading-relaxed">
                  Gives you the current citywide pulse: citywide average PM2.5, wind speed, nocturnal temperature inversion risk, and status of all 15+ monitored stations.
                </p>
              </div>

              <div className="rounded-xl border border-[#E5E5DF] bg-white p-4">
                <div className="flex items-center gap-2 text-xs font-semibold text-charcoal">
                  <Share2 className="h-4 w-4 text-brand-blue" />
                  <span>2. Neighbourhood Estimates (Virtual Sensors)</span>
                </div>
                <p className="mt-1 text-xs text-charcoal-muted leading-relaxed">
                  Solves the sensor blindspot problem. You can click any Delhi landmark (e.g. Connaught Place, Rohini, Saket) or enter any GPS coordinate to triangulate pollution from the 4 nearest anchor monitors.
                </p>
              </div>

              <div className="rounded-xl border border-[#E5E5DF] bg-white p-4">
                <div className="flex items-center gap-2 text-xs font-semibold text-charcoal">
                  <TrendingUp className="h-4 w-4 text-brand-green" />
                  <span>3. Air Quality Forecasts (1–72 Hours)</span>
                </div>
                <p className="mt-1 text-xs text-charcoal-muted leading-relaxed">
                  Select any monitoring station (e.g. Anand Vihar, Punjabi Bagh) to see predictions up to 3 days ahead. The shaded band shows the 90% confidence interval so you can assess forecast certainty.
                </p>
              </div>

              <div className="rounded-xl border border-[#E5E5DF] bg-white p-4">
                <div className="flex items-center gap-2 text-xs font-semibold text-charcoal">
                  <Sparkles className="h-4 w-4 text-[#C48A2C]" />
                  <span>4. What-if Policy Simulator & Scenario Comparison</span>
                </div>
                <p className="mt-1 text-xs text-charcoal-muted leading-relaxed">
                  Choose or compare real-world policies (e.g., Odd-Even vehicle rationing, 70% fireworks reduction, or high-wind dispersion) to immediately see how many tons of pollution are averted.
                </p>
              </div>

              <div className="rounded-xl border border-[#E5E5DF] bg-white p-4">
                <div className="flex items-center gap-2 text-xs font-semibold text-charcoal">
                  <Clock className="h-4 w-4 text-brand-blue" />
                  <span>5. Air Quality Recovery (Time-to-Clear)</span>
                </div>
                <p className="mt-1 text-xs text-charcoal-muted leading-relaxed">
                  Calculates the atmospheric half-life ($t_{1/2}$) — exactly how many hours it takes for the atmosphere to naturally flush out a toxic pollution spike based on wind ventilation.
                </p>
              </div>
            </div>
          )}

          {/* TAB 3: HEALTH & AQI */}
          {activeGuideTab === 'health' && (
            <div className="space-y-4">
              <div className="rounded-xl border border-[#E5E5DF] bg-[#FAFAF7] p-4 text-xs text-charcoal leading-relaxed">
                <span className="font-semibold block mb-1">💡 What is PM2.5 and why does it matter?</span>
                PM2.5 particles are microscopic dust particles smaller than 2.5 microns (30x thinner than a human hair). 
                Because they are so small, they penetrate deep into lungs and enter the bloodstream. 
                Indian National Standard (NAAQS) safe 24-hour limit is <strong>60 µg/m³</strong>.
              </div>

              <div className="space-y-2">
                <div className="flex items-center justify-between rounded-lg border border-[#CDE5DF] bg-[#EAF4F1] p-3 text-xs">
                  <div className="flex items-center gap-2">
                    <span className="inline-block h-3 w-3 rounded-full bg-[#3B8B77]" />
                    <strong className="text-[#285D52]">Good (0 - 50) / Satisfactory (51 - 100)</strong>
                  </div>
                  <span className="text-[#285D52] font-medium">Safe for all outdoor activities</span>
                </div>

                <div className="flex items-center justify-between rounded-lg border border-[#F5E2BE] bg-[#FDF6E9] p-3 text-xs">
                  <div className="flex items-center gap-2">
                    <span className="inline-block h-3 w-3 rounded-full bg-[#C48A2C]" />
                    <strong className="text-[#865914]">Moderate (101 - 200)</strong>
                  </div>
                  <span className="text-[#865914] font-medium">Sensitive individuals (asthma) limit intense exertion</span>
                </div>

                <div className="flex items-center justify-between rounded-lg border border-[#F6D0BA] bg-[#FDF0E9] p-3 text-xs">
                  <div className="flex items-center gap-2">
                    <span className="inline-block h-3 w-3 rounded-full bg-[#C26738]" />
                    <strong className="text-[#873A16]">Poor (201 - 300)</strong>
                  </div>
                  <span className="text-[#873A16] font-medium">Wear mask outdoors; avoid jogging during morning hours</span>
                </div>

                <div className="flex items-center justify-between rounded-lg border border-[#F5C2C2] bg-[#FCEEEE] p-3 text-xs">
                  <div className="flex items-center gap-2">
                    <span className="inline-block h-3 w-3 rounded-full bg-[#B83E3E]" />
                    <strong className="text-[#8A2424]">Very Poor (301 - 400) / Severe (401+)</strong>
                  </div>
                  <span className="text-[#8A2424] font-medium">Health alert: Everyone should wear N95, run air purifiers indoors</span>
                </div>
              </div>
            </div>
          )}

          {/* TAB 4: FAQ */}
          {activeGuideTab === 'faq' && (
            <div className="space-y-3">
              <div className="rounded-xl border border-[#E5E5DF] bg-white p-4">
                <h4 className="text-xs font-semibold text-charcoal">
                  Q: Where does AEROS get its live data?
                </h4>
                <p className="mt-1 text-xs text-charcoal-muted leading-relaxed">
                  Real-time readings come from CPCB/CAAQMS ground monitoring stations across Delhi-NCR, 
                  combined with satellite AOD from Sentinel-5P and meteorological forecasts from Open-Meteo & ERA5.
                </p>
              </div>

              <div className="rounded-xl border border-[#E5E5DF] bg-white p-4">
                <h4 className="text-xs font-semibold text-charcoal">
                  Q: Why is there a shaded gray area in the forecast chart?
                </h4>
                <p className="mt-1 text-xs text-charcoal-muted leading-relaxed">
                  That is the 90% confidence interval. Weather and emissions are dynamic, so AEROS shows both the most likely forecast value and the upper/lower bounds of certainty.
                </p>
              </div>

              <div className="rounded-xl border border-[#E5E5DF] bg-white p-4">
                <h4 className="text-xs font-semibold text-charcoal">
                  Q: Can I test my own custom neighborhood?
                </h4>
                <p className="mt-1 text-xs text-charcoal-muted leading-relaxed">
                  Yes! Go to the <strong>Neighbourhood Estimates</strong> tab and pick any landmark or type in any Delhi latitude and longitude (between 28.25°N and 29.00°N).
                </p>
              </div>
            </div>
          )}
        </div>

        {/* Modal Footer */}
        <div className="flex items-center justify-between border-t border-[#E5E5DF] bg-[#FAFAF7] px-6 py-3.5">
          <span className="text-[11px] text-charcoal-muted flex items-center gap-1">
            <CheckCircle2 className="h-3.5 w-3.5 text-brand-green" />
            Tip: You can reopen this guide anytime by clicking "Quick Guide" in the top bar.
          </span>
          <button
            onClick={onClose}
            className="rounded-lg bg-charcoal px-4 py-2 text-xs font-medium text-white transition-colors hover:bg-black"
          >
            Got it, Let's Explore!
          </button>
        </div>
      </div>
    </div>
  );
};
