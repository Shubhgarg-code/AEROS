import React from 'react';
import {
  LayoutDashboard,
  MapPin,
  TrendingUp,
  Share2,
  Wind,
  Sparkles,
  Clock,
  BarChart3,
  Cpu,
  BookOpen,
  Sun,
  Moon,
} from 'lucide-react';

export type NavTab =
  | 'overview'
  | 'live-map'
  | 'forecasting'
  | 'spatial'
  | 'propagation'
  | 'simulator'
  | 'recovery'
  | 'comparison'
  | 'models';

interface SidebarProps {
  currentTab: NavTab;
  onSelectTab: (tab: NavTab) => void;
  apiHealthy?: boolean;
  onOpenGuide?: () => void;
  theme?: 'light' | 'dark';
  onToggleTheme?: () => void;
}

export const Sidebar: React.FC<SidebarProps> = ({
  currentTab,
  onSelectTab,
  apiHealthy = true,
  onOpenGuide,
  theme = 'light',
  onToggleTheme,
}) => {
  const navItems: Array<{
    id: NavTab;
    label: string;
    icon: React.ReactNode;
    tag?: string;
    section?: string;
  }> = [
    {
      id: 'overview',
      label: 'City Overview',
      icon: <LayoutDashboard className="h-4 w-4" />,
      section: 'Live Airflow',
    },
    {
      id: 'live-map',
      label: 'Environmental Map',
      icon: <MapPin className="h-4 w-4" />,
    },
    {
      id: 'forecasting',
      label: 'Forecasts (1–72h)',
      icon: <TrendingUp className="h-4 w-4" />,
      section: 'Predictive AI',
    },
    {
      id: 'spatial',
      label: 'Virtual Sensors',
      icon: <Share2 className="h-4 w-4" />,
      tag: 'Any GPS',
    },
    {
      id: 'propagation',
      label: 'Smoke & Plume Drift',
      icon: <Wind className="h-4 w-4" />,
    },
    {
      id: 'simulator',
      label: 'What-If Policies',
      icon: <Sparkles className="h-4 w-4 text-[#C48A2C]" />,
      tag: 'Diwali',
      section: 'Policy Sandbox',
    },
    {
      id: 'recovery',
      label: 'Recovery Time',
      icon: <Clock className="h-4 w-4" />,
    },
    {
      id: 'comparison',
      label: 'Policy Benchmarks',
      icon: <BarChart3 className="h-4 w-4" />,
    },
    {
      id: 'models',
      label: 'Model Specs',
      icon: <Cpu className="h-4 w-4" />,
      section: 'System',
    },
  ];

  return (
    <aside className="flex h-screen w-64 flex-col border-r border-[#E5E5DF] bg-[#FAFAF7] text-charcoal-muted select-none">
      {/* Brand Header */}
      <div className="flex items-center gap-3 border-b border-[#E5E5DF] px-5 py-4">
        <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-[#EAF4F1] border border-[#CDE5DF] text-[#3D8B7A]">
          <Wind className="h-4 w-4" />
        </div>
        <div>
          <div className="flex items-center gap-2">
            <h1 className="font-sans text-sm font-semibold tracking-tight text-charcoal">AEROS</h1>
            <span className="rounded bg-[#F0F2EE] px-1.5 py-0.5 text-[10px] font-mono font-medium text-[#5A626A] border border-[#E5E5DF]">
              v1.7
            </span>
          </div>
          <p className="text-[11px] text-[#8C959D] font-normal leading-tight">
            Atmospheric Intelligence
          </p>
        </div>
      </div>

      {/* Navigation Links */}
      <nav className="flex-1 space-y-0.5 overflow-y-auto px-3 py-3">
        {navItems.map((item, index) => {
          const isActive = currentTab === item.id;
          return (
            <React.Fragment key={item.id}>
              {item.section && (
                <div className={`px-3 py-1.5 text-[10px] font-semibold text-[#8C959D] uppercase tracking-wider ${index > 0 ? 'mt-4' : ''}`}>
                  {item.section}
                </div>
              )}
              <button
                onClick={() => onSelectTab(item.id)}
                className={`group flex w-full items-center justify-between rounded-lg px-3 py-2 text-xs transition-all duration-150 ${
                  isActive
                    ? 'bg-white text-charcoal font-semibold shadow-[0_1px_3px_rgba(0,0,0,0.03)] border border-[#E5E5DF]'
                    : 'text-[#5A626A] hover:bg-[#F2F2EC] hover:text-charcoal border border-transparent'
                }`}
              >
                <div className="flex items-center gap-2.5">
                  <span className={`${isActive ? 'text-brand-green' : 'text-[#8C959D] group-hover:text-charcoal'}`}>
                    {item.icon}
                  </span>
                  <span>{item.label}</span>
                </div>
                {item.tag && (
                  <span
                    className={`rounded px-1.5 py-0.5 text-[9px] font-mono tracking-tight font-medium ${
                      item.tag === 'Diwali'
                        ? 'bg-[#FDF6E9] text-[#865914] border border-[#F5E2BE]'
                        : isActive
                        ? 'bg-[#EAF4F1] text-[#285D52]'
                        : 'bg-[#F0F2EE] text-[#6B7280]'
                    }`}
                  >
                    {item.tag}
                  </span>
                )}
              </button>
            </React.Fragment>
          );
        })}
      </nav>

      {/* Quick Guide Trigger */}
      {onOpenGuide && (
        <div className="p-3 border-t border-[#E5E5DF] bg-[#FAF8F5]">
          <button
            onClick={onOpenGuide}
            className="flex w-full items-center justify-between rounded-lg border border-[#CDE5DF] bg-[#EAF4F1] px-3 py-2 text-xs font-semibold text-[#285D52] hover:bg-[#d6eae4] transition-all shadow-[0_1px_2px_rgba(0,0,0,0.02)]"
          >
            <div className="flex items-center gap-2">
              <BookOpen className="h-4 w-4 text-brand-green" />
              <span>Quick Guide</span>
            </div>
            <span className="text-[10px] rounded bg-white px-1.5 py-0.5 border border-[#CDE5DF] text-brand-green font-mono">
              Help
            </span>
          </button>
        </div>
      )}

      {/* Theme Switcher in Sidebar */}
      {onToggleTheme && (
        <div className="px-3 py-2 border-t border-[#E5E5DF] bg-[#FAF8F5]">
          <button
            onClick={onToggleTheme}
            className="flex w-full items-center justify-between rounded-lg border border-[#E5E5DF] bg-white px-3 py-2 text-xs text-charcoal hover:bg-[#F2F2EC] transition-all shadow-[0_1px_2px_rgba(0,0,0,0.02)]"
            title={theme === 'dark' ? 'Switch to Light Mode' : 'Switch to Dark Mode'}
          >
            <div className="flex items-center gap-2">
              {theme === 'dark' ? (
                <Sun className="h-4 w-4 text-[#F59E0B]" />
              ) : (
                <Moon className="h-4 w-4 text-[#5A626A]" />
              )}
              <span>{theme === 'dark' ? 'Light Theme' : 'Dark Theme'}</span>
            </div>
            <span className="text-[10px] rounded bg-[#FAFAF7] px-1.5 py-0.5 border border-[#E5E5DF] text-charcoal-muted font-mono uppercase">
              {theme}
            </span>
          </button>
        </div>
      )}

      {/* Status Footer */}
      <div className="border-t border-[#E5E5DF] p-3.5 bg-[#FAF8F5]">
        <div className="flex items-center justify-between text-xs">
          <div className="flex items-center gap-2">
            <span
              className={`h-2 w-2 rounded-full ${
                apiHealthy ? 'bg-[#3D8B7A]' : 'bg-[#B83E3E]'
              }`}
            />
            <span className="text-[11px] font-medium text-charcoal-muted">
              {apiHealthy ? 'Live Connected' : 'Disconnected'}
            </span>
          </div>
          <span className="text-[10px] font-mono text-[#8C959D]">15 Stations</span>
        </div>
        <div className="mt-1 text-[10px] text-[#8C959D] flex items-center justify-between">
          <span>Delhi NCR Airshed</span>
          <span>121 Grid Cells</span>
        </div>
      </div>
    </aside>
  );
};
