import React from 'react';
import { ShieldCheck, AlertTriangle, AlertOctagon } from 'lucide-react';
import type { RiskLevel } from '../../types';

interface RiskBadgeProps {
  level: RiskLevel;
  score?: number;
  showIcon?: boolean;
  size?: 'sm' | 'md' | 'lg';
}

export const RiskBadge: React.FC<RiskBadgeProps> = ({
  level,
  score,
  showIcon = true,
  size = 'md',
}) => {
  const configs = {
    CLEAR: {
      label: 'CLEAR',
      icon: <ShieldCheck className="w-3.5 h-3.5" />,
      style: 'bg-emerald-50 text-emerald-700 border-emerald-300 shadow-xs',
      description: 'Document passes structural consistency and forensic anomaly thresholds.',
    },
    REVIEW: {
      label: 'MANUAL REVIEW',
      icon: <AlertTriangle className="w-3.5 h-3.5" />,
      style: 'bg-amber-50 text-amber-800 border-amber-300 shadow-xs',
      description: 'Requires human inspection due to expired validity, optical glare, or borderline extraction.',
    },
    HIGH_RISK: {
      label: 'HIGH RISK',
      icon: <AlertOctagon className="w-3.5 h-3.5" />,
      style: 'bg-red-50 text-red-700 border-red-300 shadow-xs',
      description: 'Critical check digit failure, severe ELA compression anomaly, or printed-vs-MRZ mismatch.',
    },
  };

  const current = configs[level] || configs.REVIEW;

  const sizeStyles = {
    sm: 'px-2 py-0.5 text-[11px] gap-1 font-medium',
    md: 'px-2.5 py-1 text-xs gap-1.5 font-semibold',
    lg: 'px-3.5 py-1.5 text-sm gap-2 font-bold',
  };

  return (
    <span
      title={current.description}
      className={`inline-flex items-center font-mono rounded-md border tracking-wide uppercase ${sizeStyles[size]} ${current.style}`}
    >
      {showIcon && current.icon}
      <span>{current.label}</span>
      {score !== undefined && (
        <span className="opacity-80 text-[10px] ml-0.5 font-normal">
          ({score.toFixed(0)})
        </span>
      )}
    </span>
  );
};
