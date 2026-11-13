import React, { useState, useEffect } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import { 
  ArrowRight, ArrowLeft, Microscope, Info
} from 'lucide-react';
import { GlassCard } from '../components/glass/GlassCard';
import { GlassButton } from '../components/glass/GlassButton';
import { EmptyState } from '../components/common/EmptyState';
import { LoadingSkeleton } from '../components/common/LoadingSkeleton';
import { ForensicImageViewer } from '../components/forensics/ForensicImageViewer';
import { screeningsApi, forensicsApi } from '../services/api';
import type { Screening, ForensicFinding, BoundingBox } from '../types';

export const ForensicLabPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();

  const [screening, setScreening] = useState<Screening | null>(null);
  const [findings, setFindings] = useState<ForensicFinding[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Active highlighted bounding box from clicked finding
  const [activeBbox, setActiveBbox] = useState<BoundingBox | null>(null);
  const [selectedFindingId, setSelectedFindingId] = useState<string | null>(null);

  useEffect(() => {
    if (!id) return;
    const fetchData = async () => {
      setIsLoading(true);
      setError(null);
      try {
        const [screenData, findingsData] = await Promise.all([
          screeningsApi.get(id),
          forensicsApi.getFindings(id),
        ]);
        setScreening(screenData);
        setFindings(findingsData);
        if (findingsData.length > 0) {
          setSelectedFindingId(findingsData[0].id);
          if (findingsData[0].region_bbox) {
            setActiveBbox(findingsData[0].region_bbox);
          }
        }
      } catch (err: any) {
        setError(err.response?.data?.detail || 'Failed to execute multi-factor forensic analysis.');
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
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
          <LoadingSkeleton className="h-[500px] w-full lg:col-span-7" />
          <LoadingSkeleton className="h-[500px] w-full lg:col-span-5" />
        </div>
      </div>
    );
  }

  if (error || !screening) {
    return (
      <EmptyState
        icon={<Microscope className="w-8 h-8" />}
        title="Forensic Data Unavailable"
        description={error || "Could not retrieve multi-factor forensic telemetry for this screening."}
        actionText="Return to Intake"
        onAction={() => navigate('/screenings/new')}
      />
    );
  }

  const criticalOrHighCount = findings.filter(
    (f) => f.severity === 'CRITICAL' || f.severity === 'HIGH'
  ).length;

  const getSeverityBadge = (severity: string) => {
    switch (severity) {
      case 'CRITICAL':
        return 'bg-red-50 text-red-700 border-red-200 font-bold';
      case 'HIGH':
        return 'bg-orange-50 text-orange-700 border-orange-200 font-semibold';
      case 'MEDIUM':
        return 'bg-amber-50 text-amber-700 border-amber-200 font-medium';
      default:
        return 'bg-blue-50 text-blue-700 border-blue-200 font-medium';
    }
  };

  const handleSelectFinding = (finding: ForensicFinding) => {
    setSelectedFindingId(finding.id);
    if (finding.region_bbox) {
      setActiveBbox(finding.region_bbox);
    } else {
      setActiveBbox(null);
    }
  };

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
            <span className="text-blue-600 font-semibold">Forensic Laboratory</span>
          </div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-900 flex items-center gap-3">
            Multi-Factor Forensic Diagnostics
            <span className={`text-xs px-2.5 py-0.5 rounded-full border ${
              criticalOrHighCount > 0 
                ? 'bg-red-50 text-red-700 border-red-200 font-semibold' 
                : 'bg-green-50 text-green-700 border-green-200 font-semibold'
            }`}>
              {criticalOrHighCount > 0 ? `${criticalOrHighCount} Anomaly Indicator(s)` : 'Baseline Consistent'}
            </span>
          </h1>
        </div>
        <div className="flex items-center gap-3">
          <GlassButton
            size="sm"
            variant="ghost"
            onClick={() => navigate(`/screenings/${id}/mrz`)}
            icon={<ArrowLeft className="w-4 h-4" />}
          >
            Back to MRZ Studio
          </GlassButton>
          <GlassButton
            size="sm"
            variant="primary"
            onClick={() => navigate(`/screenings/${id}/risk`)}
            icon={<ArrowRight className="w-4 h-4" />}
          >
            Compute Risk Assessment
          </GlassButton>
        </div>
      </div>

      {/* Mandatory Statutory Disclaimer Alert */}
      <div className="p-4 rounded-xl bg-slate-50 border border-slate-300 text-xs text-slate-700 flex items-start gap-3">
        <Info className="w-5 h-5 text-blue-600 flex-shrink-0 mt-0.5" />
        <div className="space-y-1">
          <span className="font-semibold text-slate-900 block">Evidentiary Standard & Non-Conclusive Notice</span>
          <p className="leading-relaxed text-slate-600">
            Error Level Analysis (ELA), frequency texture gradients, and metadata inspection produce probabilistic anomaly indicators. They serve as investigative clues for trained forensic examiners and do NOT constitute autonomous legal proof of fraudulent intent. Final clearance remains strictly within the authority of authorized border personnel.
          </p>
        </div>
      </div>

      {/* Main Grid: Dual Viewer & Structured Findings Registry */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left 7 Cols: Dual Viewport Viewer */}
        <div className="lg:col-span-7 space-y-4">
          <ForensicImageViewer
            originalUrl={screeningsApi.getDocumentUrl(screening.id, false)}
            heatmapUrl={forensicsApi.getHeatmapUrl(screening.id)}
            activeBbox={activeBbox}
          />
        </div>

        {/* Right 5 Cols: Structured Findings Feed */}
        <div className="lg:col-span-5 space-y-3">
          <GlassCard className="p-4 space-y-3">
            <div className="flex items-center justify-between border-b border-slate-200 pb-2">
              <h2 className="text-sm font-bold text-slate-900 flex items-center gap-1.5">
                <Microscope className="w-4 h-4 text-blue-600" />
                Forensic Diagnostics Findings ({findings.length})
              </h2>
              <span className="text-[11px] font-mono text-slate-500">5-Pillar Engine</span>
            </div>

            {/* Findings List */}
            <div className="space-y-2.5 max-h-[500px] overflow-y-auto pr-1">
              {findings.map((finding) => {
                const isSelected = finding.id === selectedFindingId;

                return (
                  <div
                    key={finding.id}
                    onClick={() => handleSelectFinding(finding)}
                    className={`p-3.5 rounded-xl border text-xs cursor-pointer transition ${
                      isSelected
                        ? 'border-blue-500 bg-blue-50/70 shadow-sm ring-1 ring-blue-400'
                        : 'border-slate-200 hover:border-slate-300 bg-white'
                    }`}
                  >
                    <div className="flex items-center justify-between mb-1.5">
                      <span className="font-mono text-[10px] text-slate-500 uppercase tracking-wider font-semibold">
                        {finding.analysis_method}
                      </span>
                      <span className={`px-2 py-0.5 rounded text-[10px] border ${getSeverityBadge(finding.severity)}`}>
                        {finding.severity}
                      </span>
                    </div>

                    <h3 className="font-semibold text-slate-900 text-sm mb-1">
                      {finding.title}
                    </h3>

                    <p className="text-slate-600 leading-relaxed line-clamp-3 mb-2">
                      {finding.explanation}
                    </p>

                    {/* Technical Parameter Pills */}
                    <div className="pt-2 border-t border-slate-200 flex flex-wrap gap-2 text-[10px] font-mono text-slate-600">
                      {Object.entries(finding.technical_details || {}).slice(0, 3).map(([k, v]) => {
                        if (typeof v === 'object') return null;
                        return (
                          <span key={k} className="bg-slate-100 px-2 py-0.5 rounded border border-slate-200">
                            {k}: {String(v)}
                          </span>
                        );
                      })}
                    </div>

                    {/* Action Hint */}
                    <div className="mt-2 text-[11px] text-blue-700 font-medium flex items-center gap-1">
                      <span>Action:</span>
                      <span className="truncate">{finding.recommended_action}</span>
                    </div>
                  </div>
                );
              })}
            </div>

            {/* Action Bar */}
            <div className="pt-3 border-t border-slate-200 flex flex-col gap-2">
              <GlassButton
                variant="primary"
                size="md"
                className="w-full justify-center"
                onClick={() => navigate(`/screenings/${id}/face`)}
                icon={<ArrowRight className="w-4 h-4" />}
              >
                Proceed to Biometric Face Match (Optional)
              </GlassButton>
              <GlassButton
                variant="ghost"
                size="sm"
                className="w-full justify-center text-xs text-slate-500 hover:text-slate-700"
                onClick={() => navigate(`/screenings/${id}/risk`)}
              >
                Skip Biometrics & Go to Risk Engine
              </GlassButton>
            </div>
          </GlassCard>
        </div>
      </div>
    </div>
  );
};
