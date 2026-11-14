import React, { useState, useEffect } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import { 
  Briefcase, ArrowLeft, Send, CheckCircle2, 
  FileText, AlertCircle, Edit3, FileDown
} from 'lucide-react';
import { GlassCard } from '../components/glass/GlassCard';
import { GlassButton } from '../components/glass/GlassButton';
import { GlassModal } from '../components/glass/GlassModal';
import { EmptyState } from '../components/common/EmptyState';
import { LoadingSkeleton } from '../components/common/LoadingSkeleton';
import { RiskBadge } from '../components/common/RiskBadge';
import { CaseStepper } from '../components/common/CaseStepper';
import { WhatNextPanel } from '../components/common/WhatNextPanel';
import { casesApi, screeningsApi, reportsApi } from '../services/api';
import type { Case, Screening, CaseStatus, CasePriority } from '../types';

export const CaseDetailPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();

  const [caseItem, setCaseItem] = useState<Case | null>(null);
  const [screening, setScreening] = useState<Screening | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // New Note state
  const [noteText, setNoteText] = useState('');
  const [isSubmittingNote, setIsSubmittingNote] = useState(false);
  const [noteError, setNoteError] = useState<string | null>(null);

  // Status Change Modal state
  const [isStatusModalOpen, setIsStatusModalOpen] = useState(false);
  const [newStatus, setNewStatus] = useState<CaseStatus>('IN_REVIEW');
  const [newPriority, setNewPriority] = useState<CasePriority>('MEDIUM');
  const [resolutionNotes, setResolutionNotes] = useState('');
  const [isUpdatingStatus, setIsUpdatingStatus] = useState(false);
  const [statusError, setStatusError] = useState<string | null>(null);
  const [isDownloadingPdf, setIsDownloadingPdf] = useState(false);

  const handleDownloadReport = async () => {
    if (!screening?.id) return;
    setIsDownloadingPdf(true);
    try {
      await reportsApi.download(screening.id, `VERISIGHT_DOSSIER_${caseItem?.case_number || screening.reference_no}.pdf`);
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Evidentiary PDF dossier generation failed.');
    } finally {
      setIsDownloadingPdf(false);
    }
  };

  const fetchCaseData = async () => {
    if (!id) return;
    setIsLoading(true);
    setError(null);
    try {
      const c = await casesApi.get(id);
      setCaseItem(c);
      setNewStatus(c.status);
      setNewPriority(c.priority);
      if (c.screening_id) {
        const s = await screeningsApi.get(c.screening_id);
        setScreening(s);
      }
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to retrieve investigation case details.');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchCaseData();
  }, [id]);

  const handleAddNote = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!id || !noteText.trim()) return;
    setIsSubmittingNote(true);
    setNoteError(null);
    try {
      const updated = await casesApi.addNote(id, noteText.trim());
      setCaseItem(updated);
      setNoteText('');
    } catch (err: any) {
      setNoteError(err.response?.data?.detail || 'Failed to affix officer note.');
    } finally {
      setIsSubmittingNote(false);
    }
  };

  const handleUpdateStatus = async () => {
    if (!id) return;
    if (newStatus === 'RESOLVED' && !resolutionNotes.trim()) {
      setStatusError('Resolution justification notes are mandatory to close an investigation.');
      return;
    }

    setIsUpdatingStatus(true);
    setStatusError(null);
    try {
      const updated = await casesApi.updateStatus(id, {
        status: newStatus,
        priority: newPriority,
        resolution_notes: resolutionNotes.trim() || undefined,
      });
      setCaseItem(updated);
      setIsStatusModalOpen(false);
    } catch (err: any) {
      setStatusError(err.response?.data?.detail || 'Failed to update investigation case status.');
    } finally {
      setIsUpdatingStatus(false);
    }
  };

  if (isLoading) {
    return (
      <div className="space-y-6 max-w-7xl mx-auto">
        <LoadingSkeleton className="h-14 w-full" />
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
          <LoadingSkeleton className="h-96 w-full lg:col-span-7" />
          <LoadingSkeleton className="h-96 w-full lg:col-span-5" />
        </div>
      </div>
    );
  }

  if (error || !caseItem) {
    return (
      <EmptyState
        icon={<Briefcase className="w-8 h-8" />}
        title="Case Dossier Unavailable"
        description={error || "Could not retrieve the specified investigation case."}
        actionText="Return to Case Queue"
        onAction={() => navigate('/cases')}
      />
    );
  }

  return (
    <div className="space-y-6 max-w-7xl mx-auto">
      {/* 6-Step Case Stepper */}
      <CaseStepper currentStep={5} screeningId={screening?.id} caseId={id} />

      {/* Recommended Next Action */}
      <WhatNextPanel
        recommendation={
          caseItem.status === 'RESOLVED'
            ? "Case is resolved. Export the official signed evidentiary dossier PDF for institutional records."
            : "Review officer notes, inspect linked evidence, and record your resolution justification."
        }
        reason={
          caseItem.status === 'RESOLVED'
            ? "The investigation determination has been locked into the cryptographic SHA-256 audit ledger."
            : "Closing an investigation requires documented officer rationale in compliance with SIH 26188 guidelines."
        }
        actionText={caseItem.status === 'RESOLVED' ? "Export Dossier PDF" : "Update Case Status"}
        onAction={caseItem.status === 'RESOLVED' ? handleDownloadReport : () => setIsStatusModalOpen(true)}
        secondaryActionText="View Risk Breakdown"
        onSecondaryAction={screening ? () => navigate(`/screenings/${screening.id}/risk`) : undefined}
        helpTopic="cases"
      />

      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-2 border-b border-slate-200">
        <div>
          <div className="flex items-center gap-2 text-xs font-medium text-slate-500 mb-1">
            <Link to="/cases" className="hover:text-blue-600">Investigation Cases</Link>
            <span>/</span>
            <span className="font-mono text-slate-800 font-bold">{caseItem.case_number}</span>
          </div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-900 flex items-center gap-3">
            Investigation Case Dossier
            <span className="text-xs px-2.5 py-0.5 rounded-full border bg-blue-50 text-blue-700 border-blue-200 font-semibold font-mono">
              Status: {caseItem.status}
            </span>
          </h1>
        </div>
        <div className="flex items-center gap-3">
          <GlassButton
            size="sm"
            variant="ghost"
            onClick={() => navigate('/cases')}
            icon={<ArrowLeft className="w-4 h-4" />}
          >
            Back to Queue
          </GlassButton>
          <GlassButton
            size="sm"
            variant="secondary"
            onClick={() => setIsStatusModalOpen(true)}
            icon={<Edit3 className="w-4 h-4" />}
          >
            Update Case Status
          </GlassButton>
          {screening && (
            <>
              <GlassButton
                size="sm"
                variant="secondary"
                onClick={handleDownloadReport}
                icon={<FileDown className="w-4 h-4" />}
                disabled={isDownloadingPdf}
              >
                {isDownloadingPdf ? 'Generating...' : 'Export Dossier PDF'}
              </GlassButton>
              <GlassButton
                size="sm"
                variant="primary"
                onClick={() => navigate(`/screenings/${screening.id}/risk`)}
                icon={<FileText className="w-4 h-4" />}
              >
                View Screening Risk
              </GlassButton>
            </>
          )}
        </div>
      </div>

      {/* Main Grid: Evidence Summary & Threaded Notes */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left 7 Cols: Credential Case Summary */}
        <div className="lg:col-span-7 space-y-6">
          <GlassCard className="p-6 space-y-4">
            <div className="flex items-center justify-between border-b border-slate-200 pb-3">
              <h2 className="text-sm font-bold text-slate-900">Case Overview & Summary</h2>
              <span className="text-xs font-mono text-slate-500">
                Priority: <span className="font-bold text-slate-900">{caseItem.priority}</span>
              </span>
            </div>

            <p className="text-xs text-slate-700 leading-relaxed font-medium">
              {caseItem.summary}
            </p>

            {caseItem.resolution_notes && (
              <div className="p-4 rounded-xl bg-green-50 border border-green-200 text-xs text-green-900 space-y-1">
                <span className="font-semibold block flex items-center gap-1.5">
                  <CheckCircle2 className="w-4 h-4 text-green-600" />
                  Resolution Dossier & Officer Findings
                </span>
                <p className="text-green-800 leading-relaxed">
                  {caseItem.resolution_notes}
                </p>
                {caseItem.resolved_at && (
                  <div className="text-[11px] font-mono text-green-600 pt-1">
                    Resolved at: {new Date(caseItem.resolved_at).toLocaleString()}
                  </div>
                )}
              </div>
            )}
          </GlassCard>

          {/* Linked Screening Evidence Card */}
          {screening && (
            <GlassCard className="p-6 space-y-4">
              <div className="flex items-center justify-between border-b border-slate-200 pb-3">
                <h2 className="text-sm font-bold text-slate-900">Linked Credential Evidence</h2>
                <RiskBadge level={screening.risk_level || 'REVIEW'} size="sm" />
              </div>

              <div className="grid grid-cols-2 sm:grid-cols-3 gap-3 text-xs">
                <div className="p-3 rounded-xl bg-slate-50 border border-slate-200">
                  <span className="text-slate-500 block font-semibold">Reference ID</span>
                  <span className="font-mono text-slate-900 font-bold block mt-1">{screening.reference_no}</span>
                </div>
                <div className="p-3 rounded-xl bg-slate-50 border border-slate-200">
                  <span className="text-slate-500 block font-semibold">Document Type</span>
                  <span className="font-mono text-slate-900 font-bold block mt-1">{screening.document_type}</span>
                </div>
                <div className="p-3 rounded-xl bg-slate-50 border border-slate-200">
                  <span className="text-slate-500 block font-semibold">Country Code</span>
                  <span className="font-mono text-slate-900 font-bold block mt-1">{screening.issuing_country_code || 'IND'}</span>
                </div>
              </div>

              {/* Image Preview Thumbnail */}
              <div className="relative rounded-xl border border-slate-200 bg-slate-950 overflow-hidden max-h-[300px] flex items-center justify-center p-2">
                <img
                  src={screeningsApi.getDocumentUrl(screening.id, true)}
                  alt="Preprocessed Evidence"
                  className="max-h-[280px] w-auto object-contain rounded"
                />
              </div>

              <div className="pt-2 flex justify-between text-xs">
                <Link
                  to={`/screenings/${screening.id}/forensics`}
                  className="text-blue-600 hover:underline font-semibold"
                >
                  Inspect Multi-Factor Forensics →
                </Link>
                <Link
                  to={`/screenings/${screening.id}/mrz`}
                  className="text-blue-600 hover:underline font-semibold"
                >
                  View MRZ Check Digits →
                </Link>
              </div>
            </GlassCard>
          )}
        </div>

        {/* Right 5 Cols: Threaded Officer Notes Desk */}
        <div className="lg:col-span-5 space-y-4">
          <GlassCard className="p-5 space-y-4">
            <div className="flex items-center justify-between border-b border-slate-200 pb-3">
              <h2 className="text-sm font-bold text-slate-900">Officer Notes & Activity Log</h2>
              <span className="text-xs font-mono text-slate-500">
                {caseItem.notes?.length || 0} Entries
              </span>
            </div>

            {/* Notes Thread */}
            <div className="space-y-3 max-h-[440px] overflow-y-auto pr-1">
              {(caseItem.notes || []).map((note, idx) => (
                <div key={idx} className="p-3 rounded-xl border border-slate-200 bg-slate-50 text-xs space-y-1">
                  <div className="flex items-center justify-between">
                    <span className="font-semibold text-slate-900">{note.author}</span>
                    <span className="font-mono text-[10px] text-slate-400">
                      {new Date(note.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                    </span>
                  </div>
                  <p className="text-slate-700 leading-relaxed">{note.text}</p>
                </div>
              ))}
            </div>

            {/* Add Note Form */}
            <form onSubmit={handleAddNote} className="pt-3 border-t border-slate-200 space-y-2">
              {noteError && (
                <div className="p-2 rounded-lg bg-red-50 text-red-700 text-xs flex items-center gap-1.5">
                  <AlertCircle className="w-3.5 h-3.5 flex-shrink-0" />
                  <span>{noteError}</span>
                </div>
              )}
              <textarea
                value={noteText}
                onChange={(e) => setNoteText(e.target.value)}
                placeholder="Log secondary inspection notes, tactile check observations, or inter-agency inquiries..."
                rows={3}
                className="w-full px-3 py-2 text-xs rounded-xl border border-slate-200 bg-white text-slate-800 focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
              <div className="flex justify-end">
                <GlassButton
                  type="submit"
                  size="sm"
                  variant="primary"
                  disabled={!noteText.trim() || isSubmittingNote}
                  icon={<Send className="w-3.5 h-3.5" />}
                >
                  {isSubmittingNote ? 'Affixing Note...' : 'Affix Officer Note'}
                </GlassButton>
              </div>
            </form>
          </GlassCard>
        </div>
      </div>

      {/* Status Transition Modal */}
      {isStatusModalOpen && (
        <GlassModal
          isOpen={true}
          onClose={() => setIsStatusModalOpen(false)}
          title={`Update Case Dossier: ${caseItem.case_number}`}
        >
          <div className="space-y-4 text-xs">
            {statusError && (
              <div className="p-3 rounded-lg bg-red-50 border border-red-200 text-red-800 flex items-center gap-2">
                <AlertCircle className="w-4 h-4 flex-shrink-0 text-red-600" />
                <span>{statusError}</span>
              </div>
            )}

            <div>
              <label className="font-semibold text-slate-700 block mb-1">
                Target Investigation Status
              </label>
              <select
                value={newStatus}
                onChange={(e) => setNewStatus(e.target.value as CaseStatus)}
                className="w-full px-3 py-2 text-xs rounded-xl border border-slate-200 bg-white text-slate-800 focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="OPEN">OPEN — Active Triage</option>
                <option value="IN_REVIEW">IN_REVIEW — Forensic Lab Underway</option>
                <option value="ESCALATED">ESCALATED — Escalated to Senior Reviewer / Intelligence</option>
                <option value="RESOLVED">RESOLVED — Formal Clearance / Verification Concluded</option>
                <option value="RETURNED">RETURNED — Inconclusive / Return to Consular Issuing Post</option>
              </select>
            </div>

            <div>
              <label className="font-semibold text-slate-700 block mb-1">
                Priority Tier
              </label>
              <select
                value={newPriority}
                onChange={(e) => setNewPriority(e.target.value as CasePriority)}
                className="w-full px-3 py-2 text-xs rounded-xl border border-slate-200 bg-white text-slate-800 focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="LOW">Low</option>
                <option value="MEDIUM">Medium</option>
                <option value="HIGH">High</option>
                <option value="URGENT">Urgent (Immediate Port Hold)</option>
              </select>
            </div>

            <div>
              <label className="font-semibold text-slate-700 block mb-1">
                Resolution Summary & Justification
              </label>
              <textarea
                value={resolutionNotes}
                onChange={(e) => setResolutionNotes(e.target.value)}
                rows={3}
                placeholder="State formal findings, consular verifications, or physical forensic test results..."
                className="w-full px-3 py-2 text-xs rounded-xl border border-slate-200 bg-white text-slate-800 focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>

            <div className="flex justify-end gap-3 pt-3 border-t border-slate-200">
              <GlassButton
                variant="ghost"
                size="sm"
                onClick={() => setIsStatusModalOpen(false)}
              >
                Cancel
              </GlassButton>
              <GlassButton
                variant="primary"
                size="sm"
                disabled={isUpdatingStatus}
                onClick={handleUpdateStatus}
                icon={<CheckCircle2 className="w-4 h-4" />}
              >
                {isUpdatingStatus ? 'Signing Update...' : 'Commit Signed Transition'}
              </GlassButton>
            </div>
          </div>
        </GlassModal>
      )}
    </div>
  );
};
