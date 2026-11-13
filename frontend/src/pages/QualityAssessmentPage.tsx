import React, { useState, useEffect } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import { 
  CheckCircle2, AlertTriangle, AlertCircle, 
  ArrowRight, ArrowLeft, Download
} from 'lucide-react';
import { GlassCard } from '../components/glass/GlassCard';
import { GlassButton } from '../components/glass/GlassButton';
import { EmptyState } from '../components/common/EmptyState';
import { LoadingSkeleton } from '../components/common/LoadingSkeleton';
import { screeningsApi } from '../services/api';
import type { Screening, QualityAssessment } from '../types';

export const QualityAssessmentPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();

  const [screening, setScreening] = useState<Screening | null>(null);
  const [quality, setQuality] = useState<QualityAssessment | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [activeImageView, setActiveImageView] = useState<'processed' | 'original'>('processed');

  useEffect(() => {
    if (!id) return;
    const fetchData = async () => {
      setIsLoading(true);
      setError(null);
      try {
        const [screenData, qualityData] = await Promise.all([
          screeningsApi.get(id),
          screeningsApi.getQuality(id),
        ]);
        setScreening(screenData);
        setQuality(qualityData);
      } catch (err: any) {
        setError(err.response?.data?.detail || 'Failed to retrieve quality assessment for this credential.');
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
          <LoadingSkeleton className="h-[400px] w-full lg:col-span-2" />
          <LoadingSkeleton className="h-[400px] w-full" />
        </div>
      </div>
    );
  }

  if (error || !screening || !quality) {
    return (
      <EmptyState
        icon={<AlertCircle className="w-8 h-8" />}
        title="Quality Record Unavailable"
        description={error || "Could not retrieve automated quality metrics for the specified credential ID."}
        actionText="Return to Intake"
        onAction={() => navigate('/screenings/new')}
      />
    );
  }

  const getScoreColor = (score: number) => {
    if (score >= 80) return 'text-green-600 bg-green-50 border-green-200';
    if (score >= 50) return 'text-amber-600 bg-amber-50 border-amber-200';
    return 'text-red-600 bg-red-50 border-red-200';
  };

  const getBlurLabel = (val: number) => {
    if (val >= 150) return { label: 'Sharp focus', status: 'pass' };
    if (val >= 100) return { label: 'Acceptable', status: 'pass' };
    return { label: 'Blur detected', status: 'fail' };
  };

  const getGlareLabel = (val: number) => {
    if (val <= 0.03) return { label: 'Low reflection', status: 'pass' };
    if (val <= 0.08) return { label: 'Moderate glare', status: 'warning' };
    return { label: 'Severe glare', status: 'fail' };
  };

  return (
    <div className="space-y-6 max-w-6xl mx-auto">
      {/* Breadcrumb & Navigation */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-2 border-b border-slate-200">
        <div>
          <div className="flex items-center gap-2 text-xs font-medium text-slate-500 mb-1">
            <Link to="/screenings" className="hover:text-blue-600">Screenings</Link>
            <span>/</span>
            <span className="font-mono text-slate-800">{screening.reference_no}</span>
            <span>/</span>
            <span className="text-blue-600 font-semibold">Optical Quality Assessment</span>
          </div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-900 flex items-center gap-3">
            Optical & Acquisition Quality Review
            <span className={`text-xs px-2.5 py-0.5 rounded-full border font-semibold ${getScoreColor(quality.overall_score)}`}>
              Overall Score: {quality.overall_score.toFixed(1)} / 100
            </span>
          </h1>
        </div>
        <div className="flex items-center gap-3">
          <GlassButton
            size="sm"
            variant="ghost"
            onClick={() => navigate('/screenings/new')}
            icon={<ArrowLeft className="w-4 h-4" />}
          >
            New Screening
          </GlassButton>
          <GlassButton
            size="sm"
            variant="primary"
            onClick={() => navigate(`/screenings/${id}/extraction`)}
            icon={<ArrowRight className="w-4 h-4" />}
          >
            Proceed to OCR Extraction
          </GlassButton>
        </div>
      </div>

      {/* Rescan Recommendation Banner */}
      {quality.rescan_recommended && (
        <div className="p-4 rounded-xl bg-amber-50 border border-amber-300 flex items-start gap-4 text-amber-900">
          <AlertTriangle className="w-6 h-6 flex-shrink-0 text-amber-600 mt-0.5" />
          <div className="space-y-1">
            <div className="font-semibold text-sm">Rescan Recommended for Evidentiary Standard</div>
            <p className="text-xs text-amber-800 leading-relaxed">
              Automated image pre-flight detected significant acquisition artifacts (e.g. motion blur, specular glare, or sub-optimal DPI). While the processing pipeline has extracted best-effort optical data, re-scanning under diffused lighting is strongly advised prior to definitive border clearance.
            </p>
          </div>
        </div>
      )}

      {/* Main Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left 2 Cols: Image Comparison Viewer */}
        <div className="lg:col-span-2 space-y-4">
          <GlassCard className="p-4">
            <div className="flex items-center justify-between mb-3 border-b border-slate-200 pb-3">
              <div className="flex items-center gap-2">
                <span className="text-xs font-semibold text-slate-700">Display Viewport:</span>
                <div className="flex rounded-lg border border-slate-200 bg-slate-100 p-0.5 text-xs font-medium">
                  <button
                    onClick={() => setActiveImageView('processed')}
                    className={`px-3 py-1 rounded-md transition ${
                      activeImageView === 'processed'
                        ? 'bg-white text-blue-700 shadow-sm font-semibold'
                        : 'text-slate-600 hover:text-slate-900'
                    }`}
                  >
                    Rectified / Preprocessed
                  </button>
                  <button
                    onClick={() => setActiveImageView('original')}
                    className={`px-3 py-1 rounded-md transition ${
                      activeImageView === 'original'
                        ? 'bg-white text-blue-700 shadow-sm font-semibold'
                        : 'text-slate-600 hover:text-slate-900'
                    }`}
                  >
                    Original Raw Scan
                  </button>
                </div>
              </div>

              <div className="text-xs font-mono text-slate-500">
                {quality.resolution_dpi} DPI Est. • {quality.orientation_detected}° Orientation
              </div>
            </div>

            {/* Document Image Surface */}
            <div className="relative rounded-xl border border-slate-200 bg-slate-900 overflow-hidden min-h-[420px] flex items-center justify-center p-2">
              <img
                src={screeningsApi.getDocumentUrl(screening.id, activeImageView === 'processed')}
                alt="Document Surface"
                className="max-h-[500px] w-auto max-w-full object-contain rounded-lg shadow-lg"
              />
              <div className="absolute bottom-3 left-3 bg-slate-900/80 backdrop-blur-md px-3 py-1 rounded-md text-[11px] font-mono text-slate-200 border border-slate-700">
                {activeImageView === 'processed' ? 'PIPELINE PREPROCESSED (DESKEWED, CLAHE)' : 'ORIGINAL TAMPER-EVIDENT EVIDENCE'}
              </div>
            </div>

            <div className="mt-3 flex items-center justify-between text-xs text-slate-500 px-1">
              <span>Non-destructive processing: original raw byte evidence is strictly retained unchanged.</span>
              <a 
                href={screeningsApi.getDocumentUrl(screening.id, false)} 
                download={`${screening.reference_no}_evidence.jpg`}
                className="text-blue-600 hover:underline flex items-center gap-1 font-medium"
              >
                <Download className="w-3.5 h-3.5" /> Download Raw File
              </a>
            </div>
          </GlassCard>
        </div>

        {/* Right Col: Quality Vector Breakdown */}
        <div className="space-y-6">
          <GlassCard className="p-5 space-y-4">
            <h2 className="text-sm font-bold text-slate-900 border-b border-slate-200 pb-2">
              Optical Quality Parameters
            </h2>

            {/* Metric Items */}
            <div className="space-y-3.5 text-xs">
              {/* Blur */}
              <div className="p-3 rounded-xl border border-slate-200 bg-slate-50/50 space-y-1.5">
                <div className="flex items-center justify-between font-semibold">
                  <span className="text-slate-700">Laplacian Sharpness Variance</span>
                  <span className={quality.blur_score >= 100 ? 'text-green-700' : 'text-red-700'}>
                    {quality.blur_score.toFixed(1)} / 100.0 Threshold
                  </span>
                </div>
                <div className="w-full h-1.5 rounded-full bg-slate-200 overflow-hidden">
                  <div 
                    className={`h-full ${quality.blur_score >= 100 ? 'bg-green-600' : 'bg-red-500'}`} 
                    style={{ width: `${Math.min(100, (quality.blur_score / 200) * 100)}%` }} 
                  />
                </div>
                <div className="text-[11px] text-slate-500 flex justify-between">
                  <span>Diagnostic: {getBlurLabel(quality.blur_score).label}</span>
                  <span>Min: 100</span>
                </div>
              </div>

              {/* Glare */}
              <div className="p-3 rounded-xl border border-slate-200 bg-slate-50/50 space-y-1.5">
                <div className="flex items-center justify-between font-semibold">
                  <span className="text-slate-700">Specular Glare Ratio</span>
                  <span className={quality.glare_score <= 0.05 ? 'text-green-700' : 'text-amber-700'}>
                    {(quality.glare_score * 100).toFixed(1)}% High Luminance
                  </span>
                </div>
                <div className="w-full h-1.5 rounded-full bg-slate-200 overflow-hidden">
                  <div 
                    className={`h-full ${quality.glare_score <= 0.05 ? 'bg-green-600' : 'bg-amber-500'}`} 
                    style={{ width: `${Math.min(100, quality.glare_score * 500)}%` }} 
                  />
                </div>
                <div className="text-[11px] text-slate-500 flex justify-between">
                  <span>Diagnostic: {getGlareLabel(quality.glare_score).label}</span>
                  <span>Threshold: &lt; 5%</span>
                </div>
              </div>

              {/* Brightness */}
              <div className="p-3 rounded-xl border border-slate-200 bg-slate-50/50 space-y-1.5">
                <div className="flex items-center justify-between font-semibold">
                  <span className="text-slate-700">Mean Luminance Level</span>
                  <span className="text-slate-900 font-mono">
                    {quality.brightness_score.toFixed(1)} / 255.0
                  </span>
                </div>
                <div className="w-full h-1.5 rounded-full bg-slate-200 overflow-hidden">
                  <div 
                    className="h-full bg-blue-600" 
                    style={{ width: `${(quality.brightness_score / 255) * 100}%` }} 
                  />
                </div>
                <div className="text-[11px] text-slate-500 flex justify-between">
                  <span>Target Range: 90 - 200</span>
                  <span>Current: {quality.brightness_score >= 80 && quality.brightness_score <= 210 ? 'Optimal' : 'Sub-optimal'}</span>
                </div>
              </div>

              {/* Readability & OCR Confidence */}
              <div className="p-3 rounded-xl border border-slate-200 bg-slate-50/50 space-y-1.5">
                <div className="flex items-center justify-between font-semibold">
                  <span className="text-slate-700">Optical Character Readability</span>
                  <span className={quality.readability_score >= 0.75 ? 'text-green-700' : 'text-amber-700'}>
                    {(quality.readability_score * 100).toFixed(1)}% Confidence
                  </span>
                </div>
                <div className="w-full h-1.5 rounded-full bg-slate-200 overflow-hidden">
                  <div 
                    className={`h-full ${quality.readability_score >= 0.75 ? 'bg-green-600' : 'bg-amber-500'}`} 
                    style={{ width: `${quality.readability_score * 100}%` }} 
                  />
                </div>
                <div className="text-[11px] text-slate-500">
                  Calculated from Tesseract character-level bounding box confidence scores.
                </div>
              </div>
            </div>

            {/* Quality Issues Flagged */}
            <div className="pt-2 border-t border-slate-200">
              <span className="text-xs font-semibold text-slate-800 block mb-2">
                Automated Quality Flags ({quality.issues_detected.length})
              </span>
              {quality.issues_detected.length === 0 ? (
                <div className="text-xs text-green-700 bg-green-50 p-2.5 rounded-xl border border-green-200 flex items-center gap-2 font-medium">
                  <CheckCircle2 className="w-4 h-4 text-green-600" />
                  No acquisition or framing anomalies detected.
                </div>
              ) : (
                <div className="space-y-1.5">
                  {quality.issues_detected.map((issue, idx) => (
                    <div key={idx} className="text-xs text-amber-800 bg-amber-50/80 p-2 rounded-lg border border-amber-200 flex items-center gap-2">
                      <AlertCircle className="w-3.5 h-3.5 text-amber-600 flex-shrink-0" />
                      <span>{issue}</span>
                    </div>
                  ))}
                </div>
              )}
            </div>

            {/* Action Bar */}
            <div className="pt-4 border-t border-slate-200 space-y-2">
              <GlassButton
                variant="primary"
                size="md"
                className="w-full justify-center"
                onClick={() => navigate(`/screenings/${id}/extraction`)}
                icon={<ArrowRight className="w-4 h-4" />}
              >
                Inspect OCR Fields
              </GlassButton>
              <GlassButton
                variant="ghost"
                size="md"
                className="w-full justify-center"
                onClick={() => navigate(`/screenings/${id}/mrz`)}
              >
                Jump to MRZ Studio
              </GlassButton>
            </div>
          </GlassCard>
        </div>
      </div>
    </div>
  );
};
