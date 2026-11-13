import React from 'react';
import { useNavigate } from 'react-router-dom';
import { AlertCircle, ArrowLeft } from 'lucide-react';
import { GlassCard } from '../components/glass/GlassCard';
import { GlassButton } from '../components/glass/GlassButton';

export const NotFoundPage: React.FC = () => {
  const navigate = useNavigate();

  return (
    <div className="min-h-screen bg-[#080F1D] flex items-center justify-center p-6">
      <GlassCard className="max-w-md w-full text-center p-8">
        <div className="w-12 h-12 rounded-xl bg-amber-500/10 text-amber-400 border border-amber-500/20 flex items-center justify-center mx-auto mb-4">
          <AlertCircle className="w-6 h-6" />
        </div>
        <h1 className="text-2xl font-bold font-mono text-slate-100">404 — NOT FOUND</h1>
        <p className="text-xs text-slate-400 mt-2 mb-6">
          The requested forensic resource, document dossier, or administrative route does not exist.
        </p>
        <GlassButton
          variant="primary"
          size="md"
          icon={<ArrowLeft className="w-4 h-4" />}
          onClick={() => navigate('/dashboard')}
        >
          Return to Command Center
        </GlassButton>
      </GlassCard>
    </div>
  );
};

