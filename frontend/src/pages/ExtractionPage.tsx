import React, { useState, useEffect, useRef } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import { 
  FileText, Edit3, ArrowRight, ArrowLeft, 
  AlertCircle, Check
} from 'lucide-react';
import { GlassCard } from '../components/glass/GlassCard';
import { GlassButton } from '../components/glass/GlassButton';
import { GlassModal } from '../components/glass/GlassModal';
import { GlassInput } from '../components/glass/GlassInput';
import { EmptyState } from '../components/common/EmptyState';
import { LoadingSkeleton } from '../components/common/LoadingSkeleton';
import { CaseStepper } from '../components/common/CaseStepper';
import { WhatNextPanel } from '../components/common/WhatNextPanel';
import { screeningsApi } from '../services/api';
import type { Screening, ExtractedField } from '../types';

export const ExtractionPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();

  const [screening, setScreening] = useState<Screening | null>(null);
  const [fields, setFields] = useState<ExtractedField[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Synchronized field highlighting
  const [activeFieldId, setActiveFieldId] = useState<string | null>(null);
  const [hoveredFieldId, setHoveredFieldId] = useState<string | null>(null);

  // Edit / Correction Modal state
  const [editingField, setEditingField] = useState<ExtractedField | null>(null);
  const [correctionValue, setCorrectionValue] = useState('');
  const [correctionNotes, setCorrectionNotes] = useState('');
  const [isSavingCorrection, setIsSavingCorrection] = useState(false);
  const [correctionError, setCorrectionError] = useState<string | null>(null);

  // Image zoom and scale tracking
  const imageContainerRef = useRef<HTMLDivElement>(null);
  const [imgNaturalSize, setImgNaturalSize] = useState<{ width: number; height: number }>({ width: 1, height: 1 });

  useEffect(() => {
    if (!id) return;
    const fetchData = async () => {
      setIsLoading(true);
      setError(null);
      try {
        const [screenData, fieldsData] = await Promise.all([
          screeningsApi.get(id),
          screeningsApi.getFields(id),
        ]);
        setScreening(screenData);
        setFields(fieldsData);
        if (fieldsData.length > 0) {
          setActiveFieldId(fieldsData[0].id);
        }
      } catch (err: any) {
        setError(err.response?.data?.detail || 'Failed to retrieve OCR extraction records.');
      } finally {
        setIsLoading(false);
      }
    };
    fetchData();
  }, [id]);

  const handleOpenCorrection = (field: ExtractedField) => {
    setEditingField(field);
    setCorrectionValue(field.current_value || '');
    setCorrectionNotes('');
    setCorrectionError(null);
  };

  const handleSaveCorrection = async () => {
    if (!editingField || !id) return;
    if (!correctionValue.trim()) {
      setCorrectionError('Value cannot be blank.');
      return;
    }
    if (!correctionNotes.trim()) {
      setCorrectionError('A justification note is strictly mandatory for evidentiary audit compliance.');
      return;
    }

    setIsSavingCorrection(true);
    setCorrectionError(null);
    try {
      const updated = await screeningsApi.correctField(id, editingField.id, {
        new_value: correctionValue.trim(),
        notes: correctionNotes.trim(),
      });
      setFields((prev) => prev.map((f) => (f.id === updated.id ? updated : f)));
      setEditingField(null);
    } catch (err: any) {
      setCorrectionError(err.response?.data?.detail || 'Failed to save correction to audit ledger.');
    } finally {
      setIsSavingCorrection(false);
    }
  };

  if (isLoading) {
    return (
      <div className="space-y-6 max-w-6xl mx-auto">
        <LoadingSkeleton className="h-14 w-full" />
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <LoadingSkeleton className="h-[450px] w-full" />
          <LoadingSkeleton className="h-[450px] w-full" />
        </div>
      </div>
    );
  }

  if (error || !screening) {
    return (
      <EmptyState
        icon={<FileText className="w-8 h-8" />}
        title="Extraction Record Unavailable"
        description={error || "Could not retrieve extracted OCR fields for the specified credential."}
        actionText="Return to Intake"
        onAction={() => navigate('/screenings/new')}
      />
    );
  }

  const activeField = fields.find((f) => f.id === (hoveredFieldId || activeFieldId));

  return (
    <div className="space-y-6 max-w-6xl mx-auto">
      {/* 6-Step Case Stepper */}
      <CaseStepper currentStep={3} screeningId={id} />

      {/* Recommended Next Action */}
      <WhatNextPanel
        recommendation="Verify extracted identity fields against document bounding boxes."
        reason="Confirm that name, birth date, document number, and nationality match the visual print before checking passport security code math."
        actionText="Proceed to MRZ Studio"
        onAction={() => navigate(`/screenings/${id}/mrz`)}
        secondaryActionText="Back to Quality"
        onSecondaryAction={() => navigate(`/screenings/${id}/quality`)}
        helpTopic="ocr"
      />

      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-2 border-b border-slate-200">
        <div>
          <div className="flex items-center gap-2 text-xs font-medium text-slate-500 mb-1">
            <Link to="/cases" className="hover:text-blue-600">Cases & Screenings</Link>
            <span>/</span>
            <span className="font-mono text-slate-800">{screening.reference_no}</span>
            <span>/</span>
            <span className="text-blue-600 font-semibold">OCR Field Extraction</span>
          </div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-900 flex items-center gap-3">
            Visual Inspection Zone (VIZ) Extraction
            <span className="text-xs px-2.5 py-0.5 rounded-full bg-blue-50 text-blue-700 border border-blue-200 font-semibold">
              {fields.length} Extracted Fields
            </span>
          </h1>
        </div>
        <div className="flex items-center gap-3">
          <GlassButton
            size="sm"
            variant="ghost"
            onClick={() => navigate(`/screenings/${id}/quality`)}
            icon={<ArrowLeft className="w-4 h-4" />}
          >
            Back to Quality
          </GlassButton>
          <GlassButton
            size="sm"
            variant="primary"
            onClick={() => navigate(`/screenings/${id}/mrz`)}
            icon={<ArrowRight className="w-4 h-4" />}
          >
            Verify MRZ Check Digits
          </GlassButton>
        </div>
      </div>

      {/* Main Grid: Bounding Box Overlay Viewer & Extracted Fields List */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left 7 Cols: Image Canvas with Interactive Bounding Boxes */}
        <div className="lg:col-span-7 space-y-3">
          <GlassCard className="p-4">
            <div className="flex items-center justify-between mb-3 text-xs text-slate-700 pb-2 border-b border-slate-200">
              <span className="font-semibold flex items-center gap-1.5">
                <FileText className="w-4 h-4 text-blue-600" />
                Synchronized Credential Surface
              </span>
              <span className="text-slate-500 font-mono">
                {activeField ? `Active: ${activeField.field_name}` : 'Click any field to localize'}
              </span>
            </div>

            {/* Canvas Container with Overlays */}
            <div 
              ref={imageContainerRef}
              className="relative rounded-xl border border-slate-200 bg-slate-950 overflow-hidden flex items-center justify-center min-h-[460px] p-2"
            >
              <div className="relative inline-block max-w-full">
                <img
                  src={screeningsApi.getDocumentUrl(screening.id, true)}
                  alt="Preprocessed Credential"
                  onLoad={(e) => {
                    const img = e.currentTarget;
                    setImgNaturalSize({ width: img.naturalWidth || 1, height: img.naturalHeight || 1 });
                  }}
                  className="max-h-[500px] w-auto max-w-full object-contain block rounded"
                />

                {/* SVG Overlay for Bounding Boxes */}
                <svg
                  className="absolute inset-0 w-full h-full pointer-events-auto"
                  viewBox={`0 0 ${imgNaturalSize.width} ${imgNaturalSize.height}`}
                  preserveAspectRatio="xMidYMid meet"
                >
                  {fields.map((field) => {
                    const bbox = field.bounding_box;
                    if (!bbox || bbox.w === 0 || bbox.h === 0) return null;
                    const isSelected = field.id === (hoveredFieldId || activeFieldId);

                    return (
                      <g
                        key={field.id}
                        className="cursor-pointer transition-all duration-150"
                        onClick={() => setActiveFieldId(field.id)}
                        onMouseEnter={() => setHoveredFieldId(field.id)}
                        onMouseLeave={() => setHoveredFieldId(null)}
                      >
                        <rect
                          x={bbox.x}
                          y={bbox.y}
                          width={bbox.w}
                          height={bbox.h}
                          fill={isSelected ? 'rgba(59, 130, 246, 0.25)' : 'rgba(34, 197, 94, 0.08)'}
                          stroke={isSelected ? '#2563EB' : '#16A34A'}
                          strokeWidth={isSelected ? 3 : 1.5}
                          rx={3}
                        />
                        {isSelected && (
                          <rect
                            x={bbox.x}
                            y={Math.max(0, bbox.y - 18)}
                            width={Math.min(180, field.field_name.length * 9 + 16)}
                            height={18}
                            fill="#1E40AF"
                            rx={2}
                          />
                        )}
                        {isSelected && (
                          <text
                            x={bbox.x + 4}
                            y={Math.max(13, bbox.y - 5)}
                            fill="#FFFFFF"
                            fontSize="11"
                            fontFamily="monospace"
                            fontWeight="bold"
                          >
                            {field.field_name}
                          </text>
                        )}
                      </g>
                    );
                  })}
                </svg>
              </div>
            </div>

            <div className="mt-3 flex items-center justify-between text-xs text-slate-500">
              <span className="flex items-center gap-1.5">
                <span className="w-2.5 h-2.5 rounded-full bg-green-500 inline-block" /> Valid Extraction Box
                <span className="w-2.5 h-2.5 rounded-full bg-blue-600 inline-block ml-3" /> Selected Field
              </span>
              <span>Click any box or field to cross-inspect</span>
            </div>
          </GlassCard>
        </div>

        {/* Right 5 Cols: Extracted Fields Table & Reviewer Controls */}
        <div className="lg:col-span-5 space-y-4">
          <GlassCard className="p-4 space-y-3">
            <div className="flex items-center justify-between border-b border-slate-200 pb-2">
              <h2 className="text-sm font-bold text-slate-900">Extracted VIZ Field Registry</h2>
              <span className="text-xs text-slate-500 font-mono">Tesseract Engine</span>
            </div>

            {/* Fields List */}
            <div className="space-y-2 max-h-[520px] overflow-y-auto pr-1">
              {fields.map((field) => {
                const isSelected = field.id === (hoveredFieldId || activeFieldId);

                return (
                  <div
                    key={field.id}
                    onClick={() => setActiveFieldId(field.id)}
                    onMouseEnter={() => setHoveredFieldId(field.id)}
                    onMouseLeave={() => setHoveredFieldId(null)}
                    className={`p-3 rounded-xl border text-xs cursor-pointer transition ${
                      isSelected
                        ? 'border-blue-500 bg-blue-50/70 shadow-sm ring-1 ring-blue-400'
                        : 'border-slate-200 hover:border-slate-300 bg-white'
                    }`}
                  >
                    <div className="flex items-center justify-between mb-1.5">
                      <div className="flex items-center gap-2">
                        <span className="font-semibold text-slate-900">{field.field_name}</span>
                        {field.is_corrected && (
                          <span className="px-1.5 py-0.5 rounded text-[10px] bg-purple-100 text-purple-800 font-medium">
                            Corrected
                          </span>
                        )}
                      </div>
                      <div className="flex items-center gap-2">
                        <span className="font-mono text-[11px] text-slate-500">
                          {field.confidence != null ? `${(field.confidence * 100).toFixed(0)}% Conf` : 'Unread'}
                        </span>
                        <button
                          type="button"
                          onClick={(e) => {
                            e.stopPropagation();
                            handleOpenCorrection(field);
                          }}
                          className="p-1 text-slate-500 hover:text-blue-600 hover:bg-blue-100 rounded transition"
                          title="Correct field value"
                        >
                          <Edit3 className="w-3.5 h-3.5" />
                        </button>
                      </div>
                    </div>

                    <div className="font-mono font-medium text-slate-800 text-sm bg-slate-50 px-2 py-1.5 rounded-lg border border-slate-100 truncate">
                      {field.current_value || <span className="text-slate-400 italic">Not detected</span>}
                    </div>

                    {field.is_corrected && (
                      <div className="mt-1 text-[11px] text-slate-500 flex items-center justify-between">
                        <span>Raw OCR: <span className="font-mono">{field.original_value}</span></span>
                        <span className="text-purple-700 italic">Reviewer modified</span>
                      </div>
                    )}
                  </div>
                );
              })}
            </div>

            {/* Reviewer Action Bar */}
            <div className="pt-3 border-t border-slate-200 space-y-2">
              <GlassButton
                variant="primary"
                size="md"
                className="w-full justify-center"
                onClick={() => navigate(`/screenings/${id}/mrz`)}
                icon={<ArrowRight className="w-4 h-4" />}
              >
                Proceed to MRZ Studio & Cross-Check
              </GlassButton>
            </div>
          </GlassCard>
        </div>
      </div>

      {/* Reviewer Field Correction Modal */}
      {editingField && (
        <GlassModal
          isOpen={true}
          onClose={() => setEditingField(null)}
          title={`Correct Field: ${editingField.field_name}`}
        >
          <div className="space-y-4 text-xs">
            {correctionError && (
              <div className="p-3 rounded-lg bg-red-50 border border-red-200 text-red-800 flex items-center gap-2">
                <AlertCircle className="w-4 h-4 flex-shrink-0 text-red-600" />
                <span>{correctionError}</span>
              </div>
            )}

            <div className="p-3 rounded-xl bg-slate-100 border border-slate-200 space-y-1">
              <span className="text-slate-500 block font-semibold">Immutable Raw Optical Value (Permanent)</span>
              <div className="font-mono text-sm text-slate-900 font-bold">{editingField.original_value}</div>
              <p className="text-[11px] text-slate-500 mt-1">
                The original optical OCR result is cryptographically preserved in the SHA-256 audit block and cannot be destroyed.
              </p>
            </div>

            <div>
              <label className="font-semibold text-slate-700 block mb-1">
                New Corrected Field Value
              </label>
              <GlassInput
                value={correctionValue}
                onChange={(e) => setCorrectionValue(e.target.value)}
                placeholder="Enter verified credential text"
                className="font-mono text-sm"
              />
            </div>

            <div>
              <label className="font-semibold text-slate-700 block mb-1">
                Mandatory Evidentiary Justification
              </label>
              <textarea
                value={correctionNotes}
                onChange={(e) => setCorrectionNotes(e.target.value)}
                rows={3}
                placeholder="State precise reason (e.g. 'Tesseract misinterpreted font character 0 as O in surname field')"
                className="w-full px-3 py-2 text-xs rounded-xl border border-slate-200 bg-white text-slate-800 focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>

            <div className="flex justify-end gap-3 pt-3 border-t border-slate-200">
              <GlassButton
                variant="ghost"
                size="sm"
                onClick={() => setEditingField(null)}
              >
                Cancel
              </GlassButton>
              <GlassButton
                variant="primary"
                size="sm"
                disabled={isSavingCorrection}
                onClick={handleSaveCorrection}
                icon={<Check className="w-4 h-4" />}
              >
                {isSavingCorrection ? 'Signing to Audit Log...' : 'Commit Immutable Correction'}
              </GlassButton>
            </div>
          </div>
        </GlassModal>
      )}
    </div>
  );
};
