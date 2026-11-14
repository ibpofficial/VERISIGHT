import React from 'react';
import { ArrowRight, HelpCircle, Lightbulb } from 'lucide-react';
import { GlassButton } from '../glass/GlassButton';
import { usePreferences } from '../../context/PreferencesContext';

interface WhatNextPanelProps {
  title?: string;
  recommendation: string;
  reason: string;
  actionText: string;
  onAction: () => void;
  secondaryActionText?: string;
  onSecondaryAction?: () => void;
  helpTopic?: string;
}

export const WhatNextPanel: React.FC<WhatNextPanelProps> = ({
  title = 'What should you do next?',
  recommendation,
  reason,
  actionText,
  onAction,
  secondaryActionText,
  onSecondaryAction,
  helpTopic,
}) => {
  const { openHelp, t } = usePreferences();

  return (
    <div className="w-full bg-gradient-to-r from-blue-50/80 via-sky-50/40 to-slate-50 border border-blue-200/90 rounded-2xl p-4 sm:p-5 shadow-xs mb-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div className="space-y-1.5 flex-1">
          <div className="flex items-center gap-2">
            <span className="p-1 rounded-md bg-blue-600 text-white shadow-xs">
              <Lightbulb className="w-4 h-4" />
            </span>
            <span className="text-xs font-bold text-blue-900 tracking-tight">
              {t('action.what_next') || title}
            </span>
            {helpTopic && (
              <button
                type="button"
                onClick={() => openHelp(helpTopic)}
                className="text-xs text-blue-600 hover:text-blue-800 flex items-center gap-1 font-medium underline ml-2"
              >
                <HelpCircle className="w-3.5 h-3.5" /> Need guidance?
              </button>
            )}
          </div>
          <h3 className="text-sm font-bold text-slate-900 leading-snug">
            {recommendation}
          </h3>
          <p className="text-xs text-slate-600 leading-relaxed max-w-3xl">
            <span className="font-semibold text-slate-800">Reason:</span> {reason}
          </p>
        </div>

        <div className="flex items-center gap-2.5 shrink-0">
          {secondaryActionText && onSecondaryAction && (
            <GlassButton
              size="sm"
              variant="secondary"
              onClick={onSecondaryAction}
            >
              {secondaryActionText}
            </GlassButton>
          )}
          <GlassButton
            size="sm"
            variant="primary"
            onClick={onAction}
            icon={<ArrowRight className="w-4 h-4" />}
          >
            {actionText}
          </GlassButton>
        </div>
      </div>
    </div>
  );
};

