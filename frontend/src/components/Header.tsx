import React from 'react';
import { RefreshCw, MapPin, BookOpen, Sun, Moon } from 'lucide-react';

interface HeaderProps {
  title: string;
  subtitle: string;
  onRefresh?: () => void;
  onOpenGuide?: () => void;
  isLoading?: boolean;
  lastUpdated?: string;
  theme?: 'light' | 'dark';
  onToggleTheme?: () => void;
}

export const Header: React.FC<HeaderProps> = ({
  title,
  subtitle,
  onRefresh,
  onOpenGuide,
  isLoading = false,
  lastUpdated,
  theme = 'light',
  onToggleTheme,
}) => {
  return (
    <header className="flex h-16 shrink-0 items-center justify-between border-b border-[#E5E5DF] bg-white/90 px-8 backdrop-blur z-10">
      <div>
        <div className="flex items-center gap-2">
          <h2 className="text-sm font-semibold tracking-tight text-charcoal">{title}</h2>
          <span className="text-[#C5C5BD]">•</span>
          <span className="text-xs text-charcoal-muted font-normal">{subtitle}</span>
        </div>
      </div>

      <div className="flex items-center gap-3">
        {onOpenGuide && (
          <button
            onClick={onOpenGuide}
            className="flex items-center gap-1.5 rounded-md border border-[#CDE5DF] bg-[#EAF4F1] px-3 py-1.5 text-xs font-semibold text-[#285D52] transition-all hover:bg-[#d5ebe5] shadow-[0_1px_2px_rgba(0,0,0,0.02)]"
            title="Open Interactive User Guide"
          >
            <BookOpen className="h-3.5 w-3.5" />
            <span>Quick Guide</span>
          </button>
        )}

        {/* Theme Toggle Button */}
        {onToggleTheme && (
          <button
            onClick={onToggleTheme}
            className="flex h-8 w-8 items-center justify-center rounded-md border border-[#E5E5DF] bg-white text-charcoal-muted hover:text-charcoal hover:bg-[#F2F2EC] transition-all shadow-[0_1px_2px_rgba(0,0,0,0.02)]"
            title={theme === 'dark' ? 'Switch to Light Mode' : 'Switch to Dark Mode'}
            aria-label="Toggle Theme"
          >
            {theme === 'dark' ? (
              <Sun className="h-4 w-4 text-[#F59E0B]" />
            ) : (
              <Moon className="h-4 w-4 text-[#5A626A]" />
            )}
          </button>
        )}

        {lastUpdated && (
          <span className="font-mono text-[11px] text-[#8C959D]">
            Updated {new Date(lastUpdated).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
          </span>
        )}

        <div className="flex items-center gap-1.5 rounded-md border border-[#E5E5DF] bg-[#FAFAF7] px-2.5 py-1 text-xs text-charcoal-muted">
          <MapPin className="h-3 w-3 text-brand-green" />
          <span>Delhi NCR</span>
        </div>

        {onRefresh && (
          <button
            onClick={onRefresh}
            disabled={isLoading}
            className="flex items-center gap-1.5 rounded-md border border-[#E5E5DF] bg-white px-3 py-1.5 text-xs font-medium text-charcoal-muted transition-colors hover:bg-[#F2F2EC] hover:text-charcoal disabled:opacity-50 shadow-[0_1px_2px_rgba(0,0,0,0.02)]"
            title="Refresh observations"
          >
            <RefreshCw className={`h-3 w-3 ${isLoading ? 'animate-spin text-brand-green' : ''}`} />
            <span>Sync</span>
          </button>
        )}
      </div>
    </header>
  );
};
