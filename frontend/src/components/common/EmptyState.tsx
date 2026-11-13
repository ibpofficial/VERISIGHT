import React from 'react';
import { GlassCard } from '../glass/GlassCard';
import { GlassButton } from '../glass/GlassButton';

interface EmptyStateProps {
  icon: React.ReactNode;
  title: string;
  description: string;
  actionText?: string;
  onAction?: () => void;
}

export const EmptyState: React.FC<EmptyStateProps> = ({
  icon,
  title,
  description,
  actionText,
  onAction,
}) => {
  return (
    <GlassCard className="text-center py-12 px-6 flex flex-col items-center justify-center">
      <div className="p-4 rounded-xl bg-blue-50 text-blue-600 border border-blue-200 mb-4 shadow-sm">
        {icon}
      </div>
      <h3 className="text-base font-semibold text-slate-900">{title}</h3>
      <p className="text-xs text-slate-600 max-w-sm mt-1 mb-6 leading-relaxed">
        {description}
      </p>
      {actionText && onAction && (
        <GlassButton variant="secondary" size="sm" onClick={onAction}>
          {actionText}
        </GlassButton>
      )}
    </GlassCard>
  );
};

