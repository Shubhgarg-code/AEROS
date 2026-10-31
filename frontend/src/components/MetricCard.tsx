import React from 'react';

interface MetricCardProps {
  title: string;
  value: string | number;
  unit?: string;
  subtitle?: string;
  trend?: {
    value: string;
    isPositive?: boolean;
    isNeutral?: boolean;
  };
  icon?: React.ReactNode;
  badge?: React.ReactNode;
  className?: string;
}

export const MetricCard: React.FC<MetricCardProps> = ({
  title,
  value,
  unit,
  subtitle,
  trend,
  icon,
  badge,
  className = '',
}) => {
  return (
    <div
      className={`relative overflow-hidden rounded-xl border border-surface-border bg-white p-5 shadow-[0_1px_3px_rgba(0,0,0,0.02)] transition-all duration-200 hover:border-[#D1D1C7] hover:shadow-[0_2px_8px_rgba(0,0,0,0.04)] ${className}`}
    >
      <div className="flex items-center justify-between text-xs font-medium text-charcoal-muted">
        <span className="flex items-center gap-2 tracking-tight">
          {icon && <span className="text-brand-green">{icon}</span>}
          <span>{title}</span>
        </span>
        {badge}
      </div>

      <div className="mt-3 flex items-baseline gap-2">
        <span className="font-mono text-3xl font-semibold tracking-tight text-charcoal">
          {value}
        </span>
        {unit && <span className="text-sm font-normal text-charcoal-muted">{unit}</span>}
      </div>

      {(subtitle || trend) && (
        <div className="mt-3 flex items-center justify-between text-xs border-t border-[#F2F2EC] pt-2.5">
          {subtitle && <span className="text-charcoal-muted leading-tight">{subtitle}</span>}
          {trend && (
            <span
              className={`font-medium ml-auto pl-2 shrink-0 ${
                trend.isNeutral
                  ? 'text-charcoal-muted'
                  : trend.isPositive
                  ? 'text-[#3D8B7A]'
                  : 'text-[#C26738]'
              }`}
            >
              {trend.value}
            </span>
          )}
        </div>
      )}
    </div>
  );
};
