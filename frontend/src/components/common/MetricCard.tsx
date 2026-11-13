import React from 'react';
import { GlassCard } from '../glass/GlassCard';

interface MetricCardProps {
  title: string;
  value: string | number;
  subtitle?: string;
  icon?: React.ReactNode;
  trend?: {
    value: string;
    isPositive?: boolean;
  };
  isSynthetic?: boolean;
}

export const MetricCard: React.FC<MetricCardProps> = ({
  title,
  value,
  subtitle,
  icon,
  trend,
  isSynthetic = false,
}) => {
  return (
    <GlassCard className="flex flex-col justify-between shadow-2xs">
      <div className="flex items-start justify-between">
        <div>
          <span className="text-xs font-semibold text-slate-500 tracking-wide uppercase font-mono">
            {title}
          </span>
          <div className="text-2xl font-bold font-mono text-slate-900 mt-1">
            {value}
          </div>
        </div>
        {icon && (
          <div className="p-2.5 rounded-lg bg-blue-50 text-blue-600 border border-blue-200/80">
            {icon}
          </div>
        )}
      </div>

      <div className="mt-4 flex items-center justify-between text-xs pt-3 border-t border-slate-100">
        {subtitle && (
          <span className="text-slate-500 font-mono text-[11px] truncate">
            {subtitle}
          </span>
        )}
        {trend && (
          <span
            className={`font-mono text-[11px] font-medium ${
              trend.isPositive ? 'text-emerald-700' : 'text-slate-500'
            }`}
          >
            {trend.value}
          </span>
        )}
        {isSynthetic && (
          <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-amber-50 text-amber-700 border border-amber-200 font-medium">
            SYNTHETIC
          </span>
        )}
      </div>
    </GlassCard>
  );
};
