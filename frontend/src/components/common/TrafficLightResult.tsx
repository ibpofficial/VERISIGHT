import React from 'react';
import { ShieldCheck, AlertTriangle, AlertOctagon, Info } from 'lucide-react';
import { usePreferences } from '../../context/PreferencesContext';
import type { RiskLevel } from '../../types';

interface TrafficLightResultProps {
  level: RiskLevel;
  score?: number;
  compact?: boolean;
}

export const TrafficLightResult: React.FC<TrafficLightResultProps> = ({
  level,
  score,
  compact = false,
}) => {
  const { t } = usePreferences();

  const configs = {
    CLEAR: {
      badgeBg: 'bg-emerald-50 text-emerald-800 border-emerald-300',
      iconBg: 'bg-emerald-500 text-white',
      icon: <ShieldCheck className="w-5 h-5" />,
      title: t('traffic.clear'),
      meaning: t('traffic.clear.meaning'),
      notMeaning: t('traffic.clear.not_meaning'),
      action: t('traffic.clear.action'),
    },
    REVIEW: {
      badgeBg: 'bg-amber-50 text-amber-800 border-amber-300',
      iconBg: 'bg-amber-500 text-white',
      icon: <AlertTriangle className="w-5 h-5" />,
      title: t('traffic.review'),
      meaning: t('traffic.review.meaning'),
      notMeaning: t('traffic.review.not_meaning'),
      action: t('traffic.review.action'),
    },
    HIGH_RISK: {
      badgeBg: 'bg-rose-50 text-rose-800 border-rose-300',
      iconBg: 'bg-rose-600 text-white',
      icon: <AlertOctagon className="w-5 h-5" />,
      title: t('traffic.high_risk'),
      meaning: t('traffic.high_risk.meaning'),
      notMeaning: t('traffic.high_risk.not_meaning'),
      action: t('traffic.high_risk.action'),
    },
  };

  const current = configs[level] || configs.REVIEW;

  if (compact) {
    return (
      <div className={`inline-flex items-center gap-2 px-3 py-1.5 rounded-full border text-xs font-bold font-mono ${current.badgeBg}`}>
        <span className="w-2 h-2 rounded-full animate-ping" />
        <span>{level.replace('_', ' ')}</span>
      </div>
    );
  }

  return (
    <div className={`p-5 rounded-2xl border ${current.badgeBg} shadow-xs space-y-4`}>
      {/* Header */}
      <div className="flex items-center justify-between border-b border-black/10 pb-3">
        <div className="flex items-center gap-3">
          <div className={`w-9 h-9 rounded-xl flex items-center justify-center shadow-xs ${current.iconBg}`}>
            {current.icon}
          </div>
          <div>
            <h3 className="text-base font-bold tracking-tight">
              {current.title}
            </h3>
            {score !== undefined && (
              <span className="text-xs font-mono font-semibold opacity-80">
                Composite Algorithmic Score: {score} / 100
              </span>
            )}
          </div>
        </div>
      </div>

      {/* 3-Point Clarification Grid */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-3 text-xs">
        <div className="p-3 rounded-xl bg-white/70 border border-black/5 space-y-1">
          <span className="font-bold block text-slate-800 uppercase tracking-wider text-[10px]">
            What this means
          </span>
          <p className="text-slate-700 leading-relaxed font-medium">
            {current.meaning}
          </p>
        </div>

        <div className="p-3 rounded-xl bg-white/70 border border-black/5 space-y-1">
          <span className="font-bold block text-slate-800 uppercase tracking-wider text-[10px]">
            What this does NOT mean
          </span>
          <p className="text-slate-700 leading-relaxed font-medium">
            {current.notMeaning}
          </p>
        </div>

        <div className="p-3 rounded-xl bg-white/70 border border-black/5 space-y-1">
          <span className="font-bold block text-slate-800 uppercase tracking-wider text-[10px]">
            Recommended officer action
          </span>
          <p className="text-slate-700 leading-relaxed font-medium">
            {current.action}
          </p>
        </div>
      </div>

      {/* Mandatory Non-Delegable Human Responsibility Notice */}
      <div className="pt-1 flex items-center gap-2 text-[11px] text-slate-600 font-medium">
        <Info className="w-3.5 h-3.5 text-blue-600 shrink-0" />
        <span>{t('disclaimer.decision_support')}</span>
      </div>
    </div>
  );
};
