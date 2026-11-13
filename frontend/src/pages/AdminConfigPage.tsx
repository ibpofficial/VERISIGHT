import React, { useState, useEffect } from 'react';
import { 
  Save, RotateCcw, Sliders, Database, AlertCircle, CheckCircle2
} from 'lucide-react';
import { GlassCard } from '../components/glass/GlassCard';
import { GlassButton } from '../components/glass/GlassButton';
import { GlassInput } from '../components/glass/GlassInput';
import { LoadingSkeleton } from '../components/common/LoadingSkeleton';
import { apiClient } from '../services/api';

export const AdminConfigPage: React.FC = () => {
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);

  // Form states
  const [highRiskThreshold, setHighRiskThreshold] = useState(65.0);
  const [reviewThreshold, setReviewThreshold] = useState(35.0);
  const [retentionDays, setRetentionDays] = useState(180);
  const [elaQuality, setElaQuality] = useState(95);

  const fetchConfig = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const res = await apiClient.get('/admin/config');
      setHighRiskThreshold(res.data.high_risk_threshold || 65.0);
      setReviewThreshold(res.data.review_threshold || 35.0);
      setRetentionDays(res.data.retention_days || 180);
      setElaQuality(res.data.ela_quality || 95);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to fetch system configuration.');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchConfig();
  }, []);

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSaving(true);
    setError(null);
    setSuccessMsg(null);
    try {
      await apiClient.patch('/admin/config', {
        high_risk_threshold: highRiskThreshold,
        review_threshold: reviewThreshold,
        retention_days: retentionDays,
        ela_quality: elaQuality,
      });
      setSuccessMsg('System configuration committed to cryptographic audit ledger.');
      setTimeout(() => setSuccessMsg(null), 4000);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to update system configuration.');
    } finally {
      setIsSaving(false);
    }
  };

  if (isLoading) {
    return (
      <div className="space-y-6 max-w-4xl mx-auto">
        <LoadingSkeleton className="h-16 w-full" />
        <LoadingSkeleton className="h-96 w-full" />
      </div>
    );
  }

  return (
    <div className="space-y-6 max-w-4xl mx-auto">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-2 border-b border-slate-200">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-900 flex items-center gap-3">
            System Risk & Threshold Configuration
            <span className="text-xs px-2.5 py-0.5 rounded-full bg-blue-50 text-blue-700 border border-blue-200 font-semibold font-mono">
              Administrative Control
            </span>
          </h1>
          <p className="text-sm text-slate-500 mt-1">
            Configure explainable risk engine scoring boundaries, forensic ELA quality levels, and retention periods.
          </p>
        </div>
        <div className="flex items-center gap-3">
          <GlassButton
            size="sm"
            variant="ghost"
            onClick={fetchConfig}
            icon={<RotateCcw className="w-4 h-4" />}
          >
            Reset
          </GlassButton>
        </div>
      </div>

      {successMsg && (
        <div className="p-3.5 rounded-xl bg-green-50 border border-green-200 text-green-800 text-xs flex items-center gap-2">
          <CheckCircle2 className="w-4 h-4 text-green-600 flex-shrink-0" />
          <span>{successMsg}</span>
        </div>
      )}

      {error && (
        <div className="p-3.5 rounded-xl bg-red-50 border border-red-200 text-red-800 text-xs flex items-center gap-2">
          <AlertCircle className="w-4 h-4 text-red-600 flex-shrink-0" />
          <span>{error}</span>
        </div>
      )}

      <form onSubmit={handleSave} className="space-y-6">
        <GlassCard className="p-6 space-y-6">
          <h2 className="text-sm font-bold text-slate-900 border-b border-slate-200 pb-3 flex items-center gap-2">
            <Sliders className="w-4 h-4 text-blue-600" />
            Deterministic Risk Classification Thresholds
          </h2>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-6 text-xs">
            <div>
              <label className="font-semibold text-slate-800 block mb-1">
                HIGH_RISK Classification Cutoff (&ge;)
              </label>
              <GlassInput
                type="number"
                step="1"
                min="50"
                max="90"
                value={highRiskThreshold}
                onChange={(e) => setHighRiskThreshold(parseFloat(e.target.value))}
              />
              <p className="text-[11px] text-slate-500 mt-1">
                Screenings with composite score &ge; this cutoff are automatically routed to HIGH RISK queue.
              </p>
            </div>

            <div>
              <label className="font-semibold text-slate-800 block mb-1">
                REVIEW Classification Cutoff (&ge;)
              </label>
              <GlassInput
                type="number"
                step="1"
                min="20"
                max="60"
                value={reviewThreshold}
                onChange={(e) => setReviewThreshold(parseFloat(e.target.value))}
              />
              <p className="text-[11px] text-slate-500 mt-1">
                Screenings between this cutoff and the High Risk cutoff require secondary inspection.
              </p>
            </div>
          </div>

          <h2 className="text-sm font-bold text-slate-900 border-b border-slate-200 pb-3 pt-4 flex items-center gap-2">
            <Database className="w-4 h-4 text-blue-600" />
            Forensics & Data Governance Policies
          </h2>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-6 text-xs">
            <div>
              <label className="font-semibold text-slate-800 block mb-1">
                Error Level Analysis Recompression Quality (1 - 100)
              </label>
              <GlassInput
                type="number"
                step="1"
                min="80"
                max="98"
                value={elaQuality}
                onChange={(e) => setElaQuality(parseInt(e.target.value))}
              />
              <p className="text-[11px] text-slate-500 mt-1">
                Standard forensic baseline is quality 95 for detecting DCT macroblock compression variance.
              </p>
            </div>

            <div>
              <label className="font-semibold text-slate-800 block mb-1">
                Evidence Data Retention Window (Days)
              </label>
              <GlassInput
                type="number"
                step="1"
                min="30"
                max="365"
                value={retentionDays}
                onChange={(e) => setRetentionDays(parseInt(e.target.value))}
              />
              <p className="text-[11px] text-slate-500 mt-1">
                Temporary image cache retention before secure purge; audit ledger hashes are preserved indefinitely.
              </p>
            </div>
          </div>

          <div className="pt-4 border-t border-slate-200 flex justify-end">
            <GlassButton
              type="submit"
              variant="primary"
              size="md"
              disabled={isSaving}
              icon={<Save className="w-4 h-4" />}
            >
              {isSaving ? 'Signing Configuration...' : 'Commit Configuration Changes'}
            </GlassButton>
          </div>
        </GlassCard>
      </form>
    </div>
  );
};
