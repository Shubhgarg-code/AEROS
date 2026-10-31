import React from 'react';
import { RefreshCw, MapPin } from 'lucide-react';

interface HeaderProps {
  title: string;
  subtitle: string;
  onRefresh?: () => void;
  isLoading?: boolean;
  lastUpdated?: string;
}

export const Header: React.FC<HeaderProps> = ({
  title,
  subtitle,
  onRefresh,
  isLoading = false,
  lastUpdated,
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
