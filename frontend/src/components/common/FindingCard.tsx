import React, { useState } from 'react';
import { 
  ChevronDown, ChevronUp, AlertCircle, CheckCircle2, 
  ShieldAlert 
} from 'lucide-react';
import { usePreferences } from '../../context/PreferencesContext';

export interface PlainFinding {
  id: string;
  category: string;
  severity: 'CRITICAL' | 'WARNING' | 'INFO';
  title: string;
  checked: string;
  found: string;
  matters: string;
  confidence: number;
  action: string;
  technicalDetails?: string;
  metadata?: Record<string, any>;
}

interface FindingCardProps {
  finding: PlainFinding;
}

export const FindingCard: React.FC<FindingCardProps> = ({ finding }) => {
  const { mode, t } = usePreferences();
  const [showTechnical, setShowTechnical] = useState(mode === 'expert');

  const severityStyles = {
    CRITICAL: {
      border: 'border-rose-200 bg-rose-50/40',
      badge: 'bg-rose-100 text-rose-800 border-rose-300',
      icon: <AlertCircle className="w-4 h-4 text-rose-600" />,
    },
    WARNING: {
      border: 'border-amber-200 bg-amber-50/40',
      badge: 'bg-amber-100 text-amber-800 border-amber-300',
      icon: <AlertCircle className="w-4 h-4 text-amber-600" />,
    },
    INFO: {
      border: 'border-slate-200 bg-white',
      badge: 'bg-slate-100 text-slate-800 border-slate-300',
      icon: <CheckCircle2 className="w-4 h-4 text-emerald-600" />,
    },
  };

  const style = severityStyles[finding.severity] || severityStyles.INFO;

  return (
    <div className={`p-4 rounded-xl border ${style.border} shadow-2xs space-y-3 transition-all`}>
      {/* Card Header */}
      <div className="flex items-center justify-between border-b border-black/5 pb-2.5">
        <div className="flex items-center gap-2">
          {style.icon}
          <h4 className="text-xs font-bold text-slate-900 tracking-tight">
            {finding.title}
          </h4>
        </div>
        <div className="flex items-center gap-2">
          <span className={`text-[10px] font-mono font-bold px-2 py-0.5 rounded-full border ${style.badge}`}>
            {finding.severity}
          </span>
          <span className="text-[10px] font-mono text-slate-500 font-semibold">
            Confidence: {Math.round(finding.confidence * 100)}%
          </span>
        </div>
      </div>

      {/* 5-Part Plain Language Structure */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5 text-xs">
        <div className="p-2.5 rounded-lg bg-white/80 border border-slate-100">
          <span className="text-[10px] uppercase font-bold text-slate-400 block tracking-wider">
            1. What we checked
          </span>
          <p className="text-slate-700 font-medium mt-0.5 leading-snug">
            {finding.checked}
          </p>
        </div>

        <div className="p-2.5 rounded-lg bg-white/80 border border-slate-100">
          <span className="text-[10px] uppercase font-bold text-slate-400 block tracking-wider">
            2. What we found
          </span>
          <p className="text-slate-900 font-bold mt-0.5 leading-snug">
            {finding.found}
          </p>
        </div>

        <div className="p-2.5 rounded-lg bg-white/80 border border-slate-100">
          <span className="text-[10px] uppercase font-bold text-slate-400 block tracking-wider">
            3. Why it matters
          </span>
          <p className="text-slate-700 font-medium mt-0.5 leading-snug">
            {finding.matters}
          </p>
        </div>

        <div className="p-2.5 rounded-lg bg-white/80 border border-slate-100">
          <span className="text-[10px] uppercase font-bold text-blue-600 block tracking-wider">
            4. What you can do
          </span>
          <p className="text-blue-900 font-semibold mt-0.5 leading-snug">
            {finding.action}
          </p>
        </div>
      </div>

      {/* Collapsible Technical Details (Simple Mode toggle / Expert Mode default) */}
      <div className="pt-1">
        <button
          type="button"
          onClick={() => setShowTechnical(!showTechnical)}
          className="text-[11px] text-slate-500 hover:text-slate-800 font-mono font-medium flex items-center gap-1"
        >
          {showTechnical ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />}
          {showTechnical ? t('action.hide_tech') : t('action.show_tech')}
        </button>

        {showTechnical && (
          <div className="mt-2 p-3 rounded-lg bg-slate-950 text-slate-200 text-[11px] font-mono space-y-1.5 border border-slate-800">
            <div className="text-sky-400 font-bold flex items-center gap-1.5">
              <ShieldAlert className="w-3.5 h-3.5" /> Engine Telemetry & Parameter Evidence
            </div>
            <p className="text-slate-300 leading-relaxed">
              {finding.technicalDetails || 'Standard heuristic boundary verification satisfied.'}
            </p>
            {finding.metadata && (
              <pre className="text-[10px] text-emerald-400 bg-black/40 p-2 rounded overflow-x-auto max-h-32">
                {JSON.stringify(finding.metadata, null, 2)}
              </pre>
            )}
          </div>
        )}
      </div>
    </div>
  );
};
