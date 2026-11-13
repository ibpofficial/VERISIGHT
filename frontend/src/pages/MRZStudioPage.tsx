import React, { useState, useEffect } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import { 
  ShieldAlert, CheckCircle2, XCircle, ArrowRight, ArrowLeft, 
  Binary
} from 'lucide-react';
import { GlassCard } from '../components/glass/GlassCard';
import { GlassButton } from '../components/glass/GlassButton';
import { EmptyState } from '../components/common/EmptyState';
import { LoadingSkeleton } from '../components/common/LoadingSkeleton';
import { screeningsApi } from '../services/api';
import type { Screening, MRZRecord, ExtractedField } from '../types';

export const MRZStudioPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();

  const [screening, setScreening] = useState<Screening | null>(null);
  const [mrz, setMrz] = useState<MRZRecord | null>(null);
  const [fields, setFields] = useState<ExtractedField[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!id) return;
    const fetchData = async () => {
      setIsLoading(true);
      setError(null);
      try {
        const [screenData, mrzData, fieldsData] = await Promise.all([
          screeningsApi.get(id),
          screeningsApi.getMRZ(id),
          screeningsApi.getFields(id),
        ]);
        setScreening(screenData);
        setMrz(mrzData);
        setFields(fieldsData);
      } catch (err: any) {
        setError(err.response?.data?.detail || 'Failed to retrieve MRZ analysis for this credential.');
      } finally {
        setIsLoading(false);
      }
    };
    fetchData();
  }, [id]);

  if (isLoading) {
    return (
      <div className="space-y-6 max-w-6xl mx-auto">
        <LoadingSkeleton className="h-14 w-full" />
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <LoadingSkeleton className="h-[350px] w-full lg:col-span-2" />
          <LoadingSkeleton className="h-[350px] w-full" />
        </div>
      </div>
    );
  }

  if (error || !screening || !mrz) {
    return (
      <EmptyState
        icon={<Binary className="w-8 h-8" />}
        title="MRZ Record Not Found"
        description={error || "No valid Machine Readable Zone could be parsed from this document scan."}
        actionText="Return to Intake"
        onAction={() => navigate('/screenings/new')}
      />
    );
  }

  const allChecksPass = mrz.doc_number_check && mrz.dob_check && mrz.expiry_check && mrz.composite_check;
  const mrzLines = mrz.raw_mrz_text.split('\n').filter(Boolean);

  const crossChecks = [
    { label: 'Document Number', mrzVal: mrz.document_number, pass: mrz.cross_check_matches?.document_number ?? true },
    { label: 'Surname', mrzVal: mrz.surname, pass: mrz.cross_check_matches?.surname ?? true },
    { label: 'Nationality Code', mrzVal: mrz.nationality, pass: mrz.cross_check_matches?.nationality ?? true },
    { label: 'Date of Birth (YYMMDD)', mrzVal: mrz.dob, pass: mrz.cross_check_matches?.dob ?? true },
    { label: 'Expiry Date (YYMMDD)', mrzVal: mrz.expiry_date, pass: mrz.cross_check_matches?.expiry_date ?? true },
  ];

  return (
    <div className="space-y-6 max-w-6xl mx-auto">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-2 border-b border-slate-200">
        <div>
          <div className="flex items-center gap-2 text-xs font-medium text-slate-500 mb-1">
            <Link to="/screenings" className="hover:text-blue-600">Screenings</Link>
            <span>/</span>
            <span className="font-mono text-slate-800">{screening.reference_no}</span>
            <span>/</span>
            <span className="text-blue-600 font-semibold">ICAO 9303 MRZ Studio</span>
          </div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-900 flex items-center gap-3">
            MRZ Verification & 7-3-1 Cryptographic Integrity
            <span className={`text-xs px-2.5 py-0.5 rounded-full border font-semibold ${
              allChecksPass
                ? 'bg-green-50 text-green-700 border-green-200'
                : 'bg-red-50 text-red-700 border-red-200'
            }`}>
              {allChecksPass ? 'All Check Digits Valid' : 'Check Digit Anomaly Detected'}
            </span>
          </h1>
        </div>
        <div className="flex items-center gap-3">
          <GlassButton
            size="sm"
            variant="ghost"
            onClick={() => navigate(`/screenings/${id}/extraction`)}
            icon={<ArrowLeft className="w-4 h-4" />}
          >
            Back to OCR Fields
          </GlassButton>
          <GlassButton
            size="sm"
            variant="primary"
            onClick={() => navigate(`/screenings/${id}/forensics`)}
            icon={<ArrowRight className="w-4 h-4" />}
          >
            Proceed to Forensics Lab
          </GlassButton>
        </div>
      </div>

      {/* Anomaly Alert if any check digit failed */}
      {!allChecksPass && (
        <div className="p-4 rounded-xl bg-red-50 border border-red-300 flex items-start gap-4 text-red-900">
          <ShieldAlert className="w-6 h-6 flex-shrink-0 text-red-600 mt-0.5" />
          <div className="space-y-1">
            <div className="font-semibold text-sm">Deterministic Check Digit Validation Failed</div>
            <p className="text-xs text-red-800 leading-relaxed">
              One or more ICAO Doc 9303 mathematical checksums (weights [7, 3, 1] modulo 10) do not match the printed check character. This indicates a counterfeit document, an altered field number, or an optical OCR scanning error requiring manual inspection.
            </p>
          </div>
        </div>
      )}

      {/* Monospaced MRZ Visualizer */}
      <GlassCard className="p-6">
        <div className="flex items-center justify-between mb-3 border-b border-slate-200 pb-2">
          <span className="text-xs font-semibold text-slate-700 flex items-center gap-2">
            <Binary className="w-4 h-4 text-blue-600" />
            ICAO Doc 9303 Standard Machine Readable Lines ({mrz.format})
          </span>
          <span className="text-xs font-mono text-slate-500">
            Issuing State: {mrz.issuing_country} • Doc Code: {mrz.doc_type_code}
          </span>
        </div>

        {/* Monospace Lines Display */}
        <div className="bg-slate-950 p-4 rounded-xl border border-slate-800 font-mono text-sm sm:text-base tracking-widest text-green-400 overflow-x-auto select-all shadow-inner">
          {mrzLines.map((line, idx) => (
            <div key={idx} className="whitespace-pre">
              {line}
            </div>
          ))}
        </div>

        {/* Legend */}
        <div className="mt-4 flex flex-wrap gap-4 text-xs text-slate-600">
          <div className="flex items-center gap-1.5">
            <span className="w-3 h-3 rounded bg-blue-100 border border-blue-400" />
            <span>Document Code</span>
          </div>
          <div className="flex items-center gap-1.5">
            <span className="w-3 h-3 rounded bg-emerald-100 border border-emerald-400" />
            <span>Holder Identity</span>
          </div>
          <div className="flex items-center gap-1.5">
            <span className="w-3 h-3 rounded bg-purple-100 border border-purple-400" />
            <span>Document Number</span>
          </div>
          <div className="flex items-center gap-1.5">
            <span className="w-3 h-3 rounded bg-amber-100 border border-amber-400" />
            <span>Check Digits (7-3-1)</span>
          </div>
        </div>
      </GlassCard>

      {/* Check Digit Breakdown Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Document Number Check */}
        <GlassCard className="p-4 space-y-2">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-slate-700">Document Number</span>
            {mrz.doc_number_check ? (
              <CheckCircle2 className="w-4 h-4 text-green-600" />
            ) : (
              <XCircle className="w-4 h-4 text-red-600" />
            )}
          </div>
          <div className="font-mono text-base font-bold text-slate-900 truncate">
            {mrz.document_number}
          </div>
          <div className="text-[11px] text-slate-500 flex justify-between pt-1 border-t border-slate-100">
            <span>Weights [7,3,1]</span>
            <span className={`font-semibold ${mrz.doc_number_check ? 'text-green-700' : 'text-red-700'}`}>
              {mrz.doc_number_check ? 'VALID DIGIT' : 'CHECKSUM MISMATCH'}
            </span>
          </div>
        </GlassCard>

        {/* Date of Birth Check */}
        <GlassCard className="p-4 space-y-2">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-slate-700">Date of Birth</span>
            {mrz.dob_check ? (
              <CheckCircle2 className="w-4 h-4 text-green-600" />
            ) : (
              <XCircle className="w-4 h-4 text-red-600" />
            )}
          </div>
          <div className="font-mono text-base font-bold text-slate-900">
            {mrz.dob}
          </div>
          <div className="text-[11px] text-slate-500 flex justify-between pt-1 border-t border-slate-100">
            <span>Sex: {mrz.sex}</span>
            <span className={`font-semibold ${mrz.dob_check ? 'text-green-700' : 'text-red-700'}`}>
              {mrz.dob_check ? 'VALID DIGIT' : 'CHECKSUM MISMATCH'}
            </span>
          </div>
        </GlassCard>

        {/* Expiry Date Check */}
        <GlassCard className="p-4 space-y-2">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-slate-700">Expiry Date</span>
            {mrz.expiry_check ? (
              <CheckCircle2 className="w-4 h-4 text-green-600" />
            ) : (
              <XCircle className="w-4 h-4 text-red-600" />
            )}
          </div>
          <div className="font-mono text-base font-bold text-slate-900">
            {mrz.expiry_date}
          </div>
          <div className="text-[11px] text-slate-500 flex justify-between pt-1 border-t border-slate-100">
            <span>ISO Format</span>
            <span className={`font-semibold ${mrz.expiry_check ? 'text-green-700' : 'text-red-700'}`}>
              {mrz.expiry_check ? 'VALID DIGIT' : 'CHECKSUM MISMATCH'}
            </span>
          </div>
        </GlassCard>

        {/* Composite Check */}
        <GlassCard className="p-4 space-y-2">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-slate-700">Composite Check</span>
            {mrz.composite_check ? (
              <CheckCircle2 className="w-4 h-4 text-green-600" />
            ) : (
              <XCircle className="w-4 h-4 text-red-600" />
            )}
          </div>
          <div className="font-mono text-sm font-bold text-slate-900 truncate">
            Composite Multi-Zone
          </div>
          <div className="text-[11px] text-slate-500 flex justify-between pt-1 border-t border-slate-100">
            <span>Overall String</span>
            <span className={`font-semibold ${mrz.composite_check ? 'text-green-700' : 'text-red-700'}`}>
              {mrz.composite_check ? 'VALID COMPOSITE' : 'COMPOSITE FAIL'}
            </span>
          </div>
        </GlassCard>
      </div>

      {/* VIZ vs MRZ Cross-Check Table */}
      <GlassCard className="p-5">
        <div className="flex items-center justify-between mb-4 border-b border-slate-200 pb-3">
          <div>
            <h2 className="text-sm font-bold text-slate-900">Visual Inspection Zone (VIZ) vs MRZ Consistency Cross-Check</h2>
            <p className="text-xs text-slate-500 mt-0.5">
              Identifies discrepancies between surface printed text and encoded machine-readable characters.
            </p>
          </div>
          <span className="text-xs font-mono text-slate-500">ICAO Section 9 Consistency</span>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-xs text-left">
            <thead>
              <tr className="border-b border-slate-200 text-slate-500 font-semibold bg-slate-50/70">
                <th className="py-2.5 px-3">Field Entity</th>
                <th className="py-2.5 px-3">Encoded MRZ Value</th>
                <th className="py-2.5 px-3">Surface Printed (VIZ) Value</th>
                <th className="py-2.5 px-3 text-right">Consistency Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {crossChecks.map((item, idx) => {
                const vizField = fields.find((f) => f.field_name.toLowerCase().includes(item.label.toLowerCase().slice(0, 5)));
                const vizVal = vizField ? vizField.current_value : '—';

                return (
                  <tr key={idx} className="hover:bg-slate-50/50 transition">
                    <td className="py-2.5 px-3 font-medium text-slate-900">{item.label}</td>
                    <td className="py-2.5 px-3 font-mono text-slate-800">{item.mrzVal}</td>
                    <td className="py-2.5 px-3 font-mono text-slate-600">{vizVal}</td>
                    <td className="py-2.5 px-3 text-right">
                      {item.pass ? (
                        <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[11px] font-semibold bg-green-50 text-green-700 border border-green-200">
                          <CheckCircle2 className="w-3 h-3" /> MATCH
                        </span>
                      ) : (
                        <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[11px] font-semibold bg-red-50 text-red-700 border border-red-200">
                          <XCircle className="w-3 h-3" /> MISMATCH
                        </span>
                      )}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </GlassCard>

      {/* Action Footer */}
      <div className="flex items-center justify-between pt-2">
        <GlassButton
          variant="ghost"
          size="md"
          onClick={() => navigate(`/screenings/${id}/extraction`)}
          icon={<ArrowLeft className="w-4 h-4" />}
        >
          Return to Extraction
        </GlassButton>
        <GlassButton
          variant="primary"
          size="md"
          onClick={() => navigate(`/screenings/${id}/forensics`)}
          icon={<ArrowRight className="w-4 h-4" />}
        >
          Proceed to Forensic Laboratory
        </GlassButton>
      </div>
    </div>
  );
};
