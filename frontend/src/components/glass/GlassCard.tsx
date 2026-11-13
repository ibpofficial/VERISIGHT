import React from 'react';
import { clsx } from 'clsx';
import { twMerge } from 'tailwind-merge';

interface GlassCardProps extends React.HTMLAttributes<HTMLDivElement> {
  children: React.ReactNode;
  hoverEffect?: boolean;
  className?: string;
}

export const GlassCard: React.FC<GlassCardProps> = ({
  children,
  hoverEffect = true,
  className,
  ...props
}) => {
  return (
    <div
      className={twMerge(
        clsx(
          'glass-panel p-5 rounded-xl border border-slate-200/80 relative overflow-hidden bg-white/85 text-slate-900',
          hoverEffect && 'hover:border-blue-400/50 hover:shadow-md transition-all duration-200',
          className
        )
      )}
      {...props}
    >
      {/* Specular Top Highlight */}
      <div className="absolute top-0 left-0 right-0 h-[1px] bg-gradient-to-r from-transparent via-white to-transparent pointer-events-none" />
      {children}
    </div>
  );
};
