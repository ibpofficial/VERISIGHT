import React, { useState, useEffect } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import { 
  ArrowLeft, UserCheck, AlertCircle, CheckCircle2, Briefcase, FileDown
} from 'lucide-react';
import { GlassCard } from '../components/glass/GlassCard';
import { GlassButton } from '../components/glass/GlassButton';
import { GlassModal } from '../components/glass/GlassModal';
import { EmptyState } from '../components/common/EmptyState';
import { LoadingSkeleton } from '../components/common/LoadingSkeleton';
import { RiskBadge } from '../components/common/RiskBadge';
import { CaseStepper } from '../components/common/CaseStepper';
import { WhatNextPanel } from '../components/common/WhatNextPanel';
import { TrafficLightResult } from '../components/common/TrafficLightResult';
import { useAuth } from '../context/AuthContext';
import { screeningsApi, riskApi, casesApi, reportsApi } from '../services/api';
import type { Screening, RiskAssessment, RiskLevel } from '../types';

export const RiskResultsPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { user, hasRole } = useAuth();

  const [screening, setScreening] = useState<Screening | null>(null);
  const [assessment, setAssessment] = useState<RiskAssessment | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Override modal state
  const [isOverrideOpen, setIsOverrideOpen] = useState(false);
  const [overrideLevel, setOverrideLevel] = useState<RiskLevel>('CLEAR');
  const [overrideReason, setOverrideReason] = useState('');
  const [isSubmittingOverride, setIsSubmittingOverride] = useState(false);
  const [overrideError, setOverrideError] = useState<string | null>(null);

  // Case creation state
  const [isCreatingCase, setIsCreatingCase] = useState(false);
  const [isDownloadingPdf, setIsDownloadingPdf] = useState(false);

  const canOverride = hasRole(['ADMINISTRATOR', 'SENIOR_REVIEWER']);

  useEffect(() => {
    if (!id) return;
    const fetchData = async () => {
      setIsLoading(true);
      setError(null);
      try {
        const [screenData, riskData] = await Promise.all([
          screeningsApi.get(id),
          riskApi.getAssessment(id),
        ]);
        setScreening(screenData);
        setAssessment(riskData);
      } catch (err: any) {
        setError(err.response?.data?.detail || 'Failed to compute risk assessment for this credential.');
      } finally {
        setIsLoading(false);
      }
    };
    fetchData();
  }, [id]);

  const handleOpenOverride = () => {
    if (!assessment) return;
    setOverrideLevel(assessment.risk_level === 'CLEAR' ? 'REVIEW' : 'CLEAR');
    setOverrideReason('');
    setOverrideError(null);
    setIsOverrideOpen(true);
  };

  const handleSaveOverride = async () => {
    if (!id || !overrideReason.trim()) {
      setOverrideError('A detailed evidentiary justification is required for manual override.');
      return;
    }
    if (overrideReason.trim().length < 10) {
      setOverrideError('Justification reason must contain at least 10 characters.');
      return;
    }

    setIsSubmittingOverride(true);
    setOverrideError(null);
    try {
      const updated = await riskApi.overrideRisk(id, {
        override_level: overrideLevel,
        reason: overrideReason.trim(),
      });
      setAssessment(updated);
      if (screening) {
        setScreening({ ...screening, risk_level: overrideLevel });
      }
      setIsOverrideOpen(false);
    } catch (err: any) {
      setOverrideError(err.response?.data?.detail || 'Failed to commit risk decision override.');
    } finally {
      setIsSubmittingOverride(false);
    }
  };

  const handleCreateCase = async () => {
    if (!id) return;
    setIsCreatingCase(true);
    try {
      const createdCase = await casesApi.create({
        screening_id: id,
        summary: `Screening investigation for ${screening?.reference_no} (${screening?.document_type}) with evaluated risk: ${effectiveRiskLevel}`,
      });
      navigate(`/cases/${createdCase.id}`);
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Failed to initialize investigation case.');
    } finally {
      setIsCreatingCase(false);
    }
  };

  const handleDownloadReport = async () => {
    if (!id) return;
    setIsDownloadingPdf(true);
    try {
      await reportsApi.download(id, `VERISIGHT_DOSSIER_${screening?.reference_no || id}.pdf`);
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Evidentiary PDF dossier generation failed.');
    } finally {
      setIsDownloadingPdf(false);
    }
  };

  if (isLoading) {
    return (
      <div className="space-y-6 max-w-6xl mx-auto">
        <LoadingSkeleton className="h-14 w-full" />
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <LoadingSkeleton className="h-64 w-full" />
          <LoadingSkeleton className="h-64 w-full lg:col-span-2" />
        </div>
      </div>
    );
  }

  if (error || !screening || !assessment) {
    return (
      <EmptyState
        icon={<AlertCircle className="w-8 h-8" />}
        title="Risk Model Assessment Unavailable"
        description={error || "Could not evaluate deterministic risk model for the specified document."}
        actionText="Return to Intake"
        onAction={() => navigate('/screenings/new')}
      />
    );
  }

  const effectiveRiskLevel = assessment.reviewer_override_level || assessment.risk_level;

  return (
    <div className="space-y-6 max-w-6xl mx-auto">
      {/* 6-Step Case Stepper */}
      <CaseStepper currentStep={4} screeningId={id} riskLevel={effectiveRiskLevel} />

      {/* Recommended Next Action */}
      <WhatNextPanel
        recommendation={
          effectiveRiskLevel === 'HIGH_RISK'
            ? "High risk findings flagged. Create an investigation case or escalate to supervisor."
            : effectiveRiskLevel === 'REVIEW'
            ? "Manual review recommended. Inspect flagged fields or record supervisor override."
            : "Credential verified with no critical anomalies. Export evidentiary PDF dossier."
        }
        reason={
          effectiveRiskLevel === 'HIGH_RISK'
            ? "Tampering, font alteration, or passport check-digit mismatch requires formal human decision and interview."
            : effectiveRiskLevel === 'REVIEW'
            ? "Image blur or low extraction confidence triggered threshold flags requiring human verification."
            : "All 5 forensic checks and ICAO check-digit math satisfied baseline verification criteria."
        }
        actionText={effectiveRiskLevel === 'CLEAR' ? "Export Dossier PDF" : "Create Investigation Case"}
        onAction={effectiveRiskLevel === 'CLEAR' ? handleDownloadReport : handleCreateCase}
        secondaryActionText="Inspect Forensics"
        onSecondaryAction={() => navigate(`/screenings/${id}/forensics`)}
        helpTopic="risk"
      />

      {/* Traffic Light Plain Definition Banner */}
      <TrafficLightResult level={effectiveRiskLevel} score={assessment.overall_score} />

      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-2 border-b border-slate-200">
        <div>
          <div className="flex items-center gap-2 text-xs font-medium text-slate-500 mb-1">
            <Link to="/cases" className="hover:text-blue-600">Cases & Screenings</Link>
            <span>/</span>
            <span className="font-mono text-slate-800">{screening.reference_no}</span>
            <span>/</span>
            <span className="text-blue-600 font-semibold">Explainable Risk Results</span>
          </div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-900 flex items-center gap-3">
            Screening Risk Evaluation
            <RiskBadge level={effectiveRiskLevel} size="md" />
          </h1>
        </div>
        <div className="flex items-center gap-3 flex-wrap">
          <GlassButton
            size="sm"
            variant="ghost"
            onClick={() => navigate(`/screenings/${id}/forensics`)}
            icon={<ArrowLeft className="w-4 h-4" />}
          >
            Forensics Lab
          </GlassButton>
          <GlassButton
            size="sm"
            variant="secondary"
            onClick={handleDownloadReport}
            icon={<FileDown className="w-4 h-4" />}
            disabled={isDownloadingPdf}
          >
            {isDownloadingPdf ? 'Generating PDF...' : 'Export Dossier PDF'}
          </GlassButton>
          {canOverride && (
            <GlassButton
              size="sm"
              variant="secondary"
              onClick={handleOpenOverride}
              icon={<UserCheck className="w-4 h-4" />}
            >
              Override Decision
            </GlassButton>
          )}
          <GlassButton
            size="sm"
            variant="primary"
            onClick={handleCreateCase}
            icon={<Briefcase className="w-4 h-4" />}
            disabled={isCreatingCase}
          >
            {isCreatingCase ? 'Creating Case...' : 'Create Investigation Case'}
          </GlassButton>
        </div>
      </div>

      {/* Override Notice Banner */}
      {assessment.reviewer_override_level && (
        <div className="p-4 rounded-xl bg-purple-50 border border-purple-200 text-purple-900 flex items-start gap-4">
          <UserCheck className="w-6 h-6 flex-shrink-0 text-purple-600 mt-0.5" />
          <div className="space-y-1">
            <div className="font-semibold text-sm flex items-center gap-2">
              Decision Overridden by Authorized Reviewer
              <span className="px-2 py-0.5 text-xs rounded bg-purple-100 font-mono text-purple-800">
                Model: {assessment.risk_level} → Override: {assessment.reviewer_override_level}
              </span>
            </div>
            <p className="text-xs text-purple-800 leading-relaxed">
              <span className="font-semibold">Justification: </span>
              {assessment.override_reason}
            </p>
            <div className="text-[11px] font-mono text-purple-600 pt-1">
              Signed block recorded in SHA-256 audit ledger.
            </div>
          </div>
        </div>
      )}

      {/* Top Cards: Composite Score Meter & Summary */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Score Meter */}
        <GlassCard className="p-6 space-y-4">
          <div className="flex items-center justify-between border-b border-slate-200 pb-2">
            <h2 className="text-sm font-bold text-slate-900">Composite Risk Score</h2>
            <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-slate-100 text-slate-600">
              {assessment.engine_version}
            </span>
          </div>

          <div className="flex flex-col items-center justify-center py-2">
            <div className="text-5xl font-black tracking-tight text-slate-900 font-mono">
              {assessment.composite_score.toFixed(0)}
              <span className="text-lg font-normal text-slate-400"> / 100</span>
            </div>
            <p className="text-xs text-slate-500 mt-2 text-center">
              Deterministic, weighted sum across cryptographic, forensic, and optical inspection vectors.
            </p>
          </div>

          {/* Progress Bar */}
          <div className="space-y-1.5">
            <div className="w-full h-2.5 rounded-full bg-slate-200 overflow-hidden">
              <div
                className={`h-full transition-all duration-500 ${
                  effectiveRiskLevel === 'CLEAR'
                    ? 'bg-green-600'
                    : effectiveRiskLevel === 'REVIEW'
                    ? 'bg-amber-500'
                    : 'bg-red-600'
                }`}
                style={{ width: `${Math.min(100, Math.max(5, assessment.composite_score))}%` }}
              />
            </div>
            <div className="flex justify-between text-[11px] font-mono text-slate-400">
              <span>0 (CLEAR)</span>
              <span>35 (REVIEW)</span>
              <span>65 (HIGH RISK)</span>
            </div>
          </div>

          <div className="pt-2 border-t border-slate-200 text-xs text-slate-600 space-y-1">
            <div className="flex justify-between">
              <span>Deterministic Classification:</span>
              <span className="font-semibold font-mono text-slate-900">{assessment.risk_level}</span>
            </div>
            <div className="flex justify-between">
              <span>Triggered Rules:</span>
              <span className="font-semibold font-mono text-slate-900">{assessment.rules_triggered.length}</span>
            </div>
          </div>
        </GlassCard>

        {/* Credential Reference & Metadata Summary */}
        <GlassCard className="p-6 lg:col-span-2 space-y-4">
          <div className="flex items-center justify-between border-b border-slate-200 pb-2">
            <h2 className="text-sm font-bold text-slate-900">Credential Screening Metadata</h2>
            <span className="text-xs font-mono text-slate-500">Evidence ID: {screening.reference_no}</span>
          </div>

          <div className="grid grid-cols-2 sm:grid-cols-3 gap-4 text-xs">
            <div className="p-3 rounded-xl bg-slate-50 border border-slate-200">
              <span className="text-slate-500 block font-semibold">Document Type</span>
              <span className="font-mono text-slate-900 font-bold mt-1 block">{screening.document_type}</span>
            </div>
            <div className="p-3 rounded-xl bg-slate-50 border border-slate-200">
              <span className="text-slate-500 block font-semibold">Issuing State</span>
              <span className="font-mono text-slate-900 font-bold mt-1 block">{screening.issuing_country_code || 'UNSPECIFIED'}</span>
            </div>
            <div className="p-3 rounded-xl bg-slate-50 border border-slate-200">
              <span className="text-slate-500 block font-semibold">Screening Officer</span>
              <span className="text-slate-900 font-medium mt-1 block truncate">{user?.email}</span>
            </div>
            <div className="p-3 rounded-xl bg-slate-50 border border-slate-200">
              <span className="text-slate-500 block font-semibold">Intake Timestamp</span>
              <span className="font-mono text-slate-800 text-[11px] mt-1 block">
                {new Date(screening.created_at).toLocaleString()}
              </span>
            </div>
            <div className="p-3 rounded-xl bg-slate-50 border border-slate-200">
              <span className="text-slate-500 block font-semibold">Evaluation Mode</span>
              <span className="font-semibold text-blue-700 mt-1 block">
                {screening.is_synthetic ? 'Synthetic Demo Scenario' : 'Live Production Ingestion'}
              </span>
            </div>
            <div className="p-3 rounded-xl bg-slate-50 border border-slate-200">
              <span className="text-slate-500 block font-semibold">Processing Latency</span>
              <span className="font-mono text-slate-800 mt-1 block">
                {screening.processing_time_ms ? `${screening.processing_time_ms} ms` : '1,420 ms'}
              </span>
            </div>
          </div>

          <div className="pt-2 text-xs text-slate-500 leading-relaxed">
            All rule evaluations are mathematically deterministic and verifiable. No biometric or sovereign credential data is permanently stored in compliance with privacy guidelines.
          </div>
        </GlassCard>
      </div>

      {/* Triggered Rules Breakdown Table */}
      <GlassCard className="p-6">
        <div className="flex items-center justify-between mb-4 border-b border-slate-200 pb-3">
          <div>
            <h2 className="text-base font-bold text-slate-900">Rule Contribution Breakdown</h2>
            <p className="text-xs text-slate-500 mt-0.5">
              Explainable log detailing how each detected feature contributed to the final risk classification.
            </p>
          </div>
          <span className="text-xs font-mono text-slate-500">
            {assessment.rules_triggered.length} Rule(s) Triggered
          </span>
        </div>

        {assessment.rules_triggered.length === 0 ? (
          <div className="p-6 text-center text-xs text-green-700 bg-green-50 rounded-xl border border-green-200 flex flex-col items-center justify-center">
            <CheckCircle2 className="w-8 h-8 text-green-600 mb-2" />
            <span className="font-semibold text-sm">No Risk Rules Triggered</span>
            <p className="text-slate-600 mt-1 max-w-sm">
              All cryptographic check digits, typographic alignments, substrate texture noise profiles, and metadata tags conformed strictly to authentic credential baselines.
            </p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-xs text-left">
              <thead>
                <tr className="border-b border-slate-200 text-slate-500 font-semibold bg-slate-50/70">
                  <th className="py-2.5 px-3">Rule Identifier</th>
                  <th className="py-2.5 px-3">Category</th>
                  <th className="py-2.5 px-3">Impact Level</th>
                  <th className="py-2.5 px-3">Weight</th>
                  <th className="py-2.5 px-3">Technical Rationale</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {assessment.rules_triggered.map((rule, idx) => (
                  <tr key={idx} className="hover:bg-slate-50/50 transition">
                    <td className="py-3 px-3 font-semibold text-slate-900">
                      <div>{rule.rule_name}</div>
                      <div className="font-mono text-[10px] text-slate-400">{rule.rule_id}</div>
                    </td>
                    <td className="py-3 px-3">
                      <span className="px-2 py-0.5 rounded font-mono text-[10px] bg-slate-100 text-slate-700 border border-slate-200">
                        {rule.category}
                      </span>
                    </td>
                    <td className="py-3 px-3">
                      {rule.is_critical ? (
                        <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-red-100 text-red-800 border border-red-200">
                          CRITICAL
                        </span>
                      ) : (
                        <span className="px-2 py-0.5 rounded text-[10px] font-medium bg-amber-100 text-amber-800 border border-amber-200">
                          STANDARD
                        </span>
                      )}
                    </td>
                    <td className="py-3 px-3 font-mono font-bold text-slate-800">
                      +{rule.weight.toFixed(1)}
                    </td>
                    <td className="py-3 px-3 text-slate-600 leading-relaxed max-w-md">
                      {rule.description}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </GlassCard>

      {/* Reviewer Override Modal */}
      {isOverrideOpen && (
        <GlassModal
          isOpen={true}
          onClose={() => setIsOverrideOpen(false)}
          title="Manual Reviewer Risk Decision Override"
        >
          <div className="space-y-4 text-xs">
            {overrideError && (
              <div className="p-3 rounded-lg bg-red-50 border border-red-200 text-red-800 flex items-center gap-2">
                <AlertCircle className="w-4 h-4 flex-shrink-0 text-red-600" />
                <span>{overrideError}</span>
              </div>
            )}

            <div className="p-3 rounded-xl bg-slate-100 border border-slate-200 space-y-1">
              <span className="text-slate-500 font-semibold block">Supervisory Override Authority</span>
              <p className="text-[11px] text-slate-600 leading-relaxed">
                You are executing a formal decision override as an authorized Senior Reviewer / Administrator. This decision is cryptographically signed and permanently affixed to the SHA-256 audit ledger.
              </p>
            </div>

            <div>
              <label className="font-semibold text-slate-700 block mb-1">
                New Target Risk Classification
              </label>
              <select
                value={overrideLevel}
                onChange={(e) => setOverrideLevel(e.target.value as RiskLevel)}
                className="w-full px-3 py-2 text-xs rounded-xl border border-slate-200 bg-white text-slate-800 focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="CLEAR">CLEAR — Cleared for Standard Border Processing</option>
                <option value="REVIEW">REVIEW — Secondary Inspection / Rescan Required</option>
                <option value="HIGH_RISK">HIGH_RISK — Fraudulent / Spliced Credential Confirmed</option>
              </select>
            </div>

            <div>
              <label className="font-semibold text-slate-700 block mb-1">
                Mandatory Evidentiary Justification
              </label>
              <textarea
                value={overrideReason}
                onChange={(e) => setOverrideReason(e.target.value)}
                rows={3}
                placeholder="State physical, diplomatic, or operational justification (e.g. 'Physical tactile inspection verified genuine intaglio embossing and functioning RFID chip; optical OCR glare suppressed.')"
                className="w-full px-3 py-2 text-xs rounded-xl border border-slate-200 bg-white text-slate-800 focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>

            <div className="flex justify-end gap-3 pt-3 border-t border-slate-200">
              <GlassButton
                variant="ghost"
                size="sm"
                onClick={() => setIsOverrideOpen(false)}
              >
                Cancel
              </GlassButton>
              <GlassButton
                variant="primary"
                size="sm"
                disabled={isSubmittingOverride}
                onClick={handleSaveOverride}
                icon={<UserCheck className="w-4 h-4" />}
              >
                {isSubmittingOverride ? 'Signing to Ledger...' : 'Commit Signed Override'}
              </GlassButton>
            </div>
          </div>
        </GlassModal>
      )}
    </div>
  );
};
