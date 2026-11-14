import React from 'react';
import { useNavigate } from 'react-router-dom';
import { 
  CheckCircle2, Clock, AlertTriangle, Circle, 
  FilePlus, Upload, ShieldCheck, Eye, Search, FileText 
} from 'lucide-react';
import { usePreferences } from '../../context/PreferencesContext';

export type StepStatus = 'done' | 'in_progress' | 'needs_attention' | 'not_started';

export interface StepInfo {
  step: number;
  id: string;
  titleKey: string;
  defaultTitle: string;
  descKey: string;
  defaultDesc: string;
  status: StepStatus;
  route?: string;
  icon: React.ReactNode;
}

interface CaseStepperProps {
  currentStep: number;
  screeningId?: string;
  caseId?: string;
  riskLevel?: 'CLEAR' | 'REVIEW' | 'HIGH_RISK';
}

export const CaseStepper: React.FC<CaseStepperProps> = ({
  currentStep,
  screeningId,
  caseId,
  riskLevel,
}) => {
  const navigate = useNavigate();
  const { t } = usePreferences();

  const getStatusForStep = (stepNumber: number): StepStatus => {
    if (stepNumber < currentStep) return 'done';
    if (stepNumber === currentStep) {
      if (riskLevel === 'HIGH_RISK') return 'needs_attention';
      return 'in_progress';
    }
    return 'not_started';
  };

  const steps: StepInfo[] = [
    {
      step: 1,
      id: 'create',
      titleKey: 'step.1',
      defaultTitle: '1. Create Case',
      descKey: 'step.1.desc',
      defaultDesc: 'Screening intake & reference generation',
      status: getStatusForStep(1),
      route: '/screenings/new',
      icon: <FilePlus className="w-3.5 h-3.5" />,
    },
    {
      step: 2,
      id: 'documents',
      titleKey: 'step.2',
      defaultTitle: '2. Add Documents',
      descKey: 'step.2.desc',
      defaultDesc: 'Quality, glare, and sharpness pre-flight',
      status: getStatusForStep(2),
      route: screeningId ? `/screenings/${screeningId}/quality` : '/screenings/new',
      icon: <Upload className="w-3.5 h-3.5" />,
    },
    {
      step: 3,
      id: 'checks',
      titleKey: 'step.3',
      defaultTitle: '3. Automatic Checks',
      descKey: 'step.3.desc',
      defaultDesc: 'OCR text and passport math checks',
      status: getStatusForStep(3),
      route: screeningId ? `/screenings/${screeningId}/mrz` : undefined,
      icon: <ShieldCheck className="w-3.5 h-3.5" />,
    },
    {
      step: 4,
      id: 'findings',
      titleKey: 'step.4',
      defaultTitle: '4. Review Findings',
      descKey: 'step.4.desc',
      defaultDesc: 'Tamper heatmaps & risk evaluation',
      status: getStatusForStep(4),
      route: screeningId ? `/screenings/${screeningId}/risk` : undefined,
      icon: <Eye className="w-3.5 h-3.5" />,
    },
    {
      step: 5,
      id: 'investigate',
      titleKey: 'step.5',
      defaultTitle: '5. Investigate & Decide',
      descKey: 'step.5.desc',
      defaultDesc: 'Officer notes & investigation status',
      status: getStatusForStep(5),
      route: caseId ? `/cases/${caseId}` : '/cases',
      icon: <Search className="w-3.5 h-3.5" />,
    },
    {
      step: 6,
      id: 'report',
      titleKey: 'step.6',
      defaultTitle: '6. Final Dossier',
      descKey: 'step.6.desc',
      defaultDesc: 'Evidentiary report & audit lock',
      status: getStatusForStep(6),
      route: caseId ? `/cases/${caseId}` : undefined,
      icon: <FileText className="w-3.5 h-3.5" />,
    },
  ];

  const getStatusBadge = (status: StepStatus) => {
    switch (status) {
      case 'done':
        return (
          <span className="inline-flex items-center gap-1 text-[10px] font-semibold text-emerald-700 bg-emerald-50 px-1.5 py-0.5 rounded border border-emerald-200">
            <CheckCircle2 className="w-3 h-3 text-emerald-600" /> Done
          </span>
        );
      case 'in_progress':
        return (
          <span className="inline-flex items-center gap-1 text-[10px] font-semibold text-blue-700 bg-blue-50 px-1.5 py-0.5 rounded border border-blue-200 animate-pulse">
            <Clock className="w-3 h-3 text-blue-600" /> In Progress
          </span>
        );
      case 'needs_attention':
        return (
          <span className="inline-flex items-center gap-1 text-[10px] font-semibold text-rose-700 bg-rose-50 px-1.5 py-0.5 rounded border border-rose-200">
            <AlertTriangle className="w-3 h-3 text-rose-600" /> Attention
          </span>
        );
      case 'not_started':
      default:
        return (
          <span className="inline-flex items-center gap-1 text-[10px] font-medium text-slate-400 bg-slate-50 px-1.5 py-0.5 rounded border border-slate-200">
            <Circle className="w-2.5 h-2.5 text-slate-300" /> Pending
          </span>
        );
    }
  };

  return (
    <div className="w-full bg-white/90 backdrop-blur-md rounded-2xl border border-slate-200/80 p-4 shadow-xs mb-6 select-none">
      {/* Top Meta Line */}
      <div className="flex items-center justify-between pb-3 mb-3 border-b border-slate-100">
        <div className="flex items-center gap-2">
          <span className="text-[11px] font-mono font-bold tracking-wider uppercase text-blue-700">
            Verification Story
          </span>
          <span className="text-slate-300">•</span>
          <span className="text-xs font-semibold text-slate-700">
            Step {currentStep} of 6: {steps[currentStep - 1]?.defaultTitle.replace(/^\d+\.\s*/, '')}
          </span>
        </div>
        <div className="text-[11px] text-slate-500 font-medium">
          Click any completed step to review its evidence
        </div>
      </div>

      {/* Stepper Grid */}
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-2">
        {steps.map((s) => {
          const isCurrent = s.step === currentStep;
          const isClickable = !!s.route && s.step <= currentStep + 1;

          return (
            <button
              key={s.id}
              type="button"
              disabled={!isClickable}
              onClick={() => s.route && navigate(s.route)}
              className={`text-left p-2.5 rounded-xl transition-all duration-150 border flex flex-col justify-between ${
                isCurrent
                  ? 'bg-blue-50/70 border-blue-300 shadow-xs ring-1 ring-blue-400/30'
                  : s.status === 'done'
                  ? 'bg-slate-50/60 hover:bg-slate-100/70 border-slate-200 cursor-pointer'
                  : 'bg-white/40 border-slate-100 opacity-60 cursor-not-allowed'
              }`}
            >
              <div>
                <div className="flex items-center justify-between mb-1.5">
                  <div className={`p-1 rounded-md ${isCurrent ? 'bg-blue-600 text-white' : 'bg-slate-200 text-slate-700'}`}>
                    {s.icon}
                  </div>
                  {getStatusBadge(s.status)}
                </div>
                <div className="text-xs font-bold text-slate-800 line-clamp-1">
                  {t(s.titleKey)}
                </div>
              </div>
              <div className="text-[10px] text-slate-500 line-clamp-1 mt-1 leading-tight">
                {t(s.descKey)}
              </div>
            </button>
          );
        })}
      </div>
    </div>
  );
};
