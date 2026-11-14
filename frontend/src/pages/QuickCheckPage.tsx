import React, { useState, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { 
  Zap, Upload, FileText, CheckCircle2, AlertTriangle, 
  ShieldAlert, RefreshCw, Layers, Clock, Eye, Briefcase, 
  ArrowRight, Download, Info, FileSpreadsheet
} from 'lucide-react';
import { GlassCard } from '../components/glass/GlassCard';
import { GlassButton } from '../components/glass/GlassButton';
import { FindingCard } from '../components/common/FindingCard';
import { quickCheckApi } from '../services/api';
import { usePreferences } from '../context/PreferencesContext';

export const QuickCheckPage: React.FC = () => {
  const navigate = useNavigate();
  const fileInputRef = useRef<HTMLInputElement>(null);
  const { mode, t } = usePreferences();

  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [analysisResult, setAnalysisResult] = useState<any | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [activeLayer, setActiveLayer] = useState<'original' | 'ela'>('ela');
  const [isEscalating, setIsEscalating] = useState(false);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      const file = e.target.files[0];
      setSelectedFile(file);
      setAnalysisResult(null);
      setErrorMessage(null);
    }
  };

  const handleDrop = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      const file = e.dataTransfer.files[0];
      setSelectedFile(file);
      setAnalysisResult(null);
      setErrorMessage(null);
    }
  };

  const handleRunAnalysis = async (fileToAnalyze?: File) => {
    const target = fileToAnalyze || selectedFile;
    if (!target) return;
    setIsAnalyzing(true);
    setErrorMessage(null);
    try {
      const res = await quickCheckApi.upload(target);
      setAnalysisResult(res);
    } catch (err: any) {
      setErrorMessage(err.response?.data?.detail || 'Quick check forensic processing failed.');
    } finally {
      setIsAnalyzing(false);
    }
  };

  const handleEscalateToCase = async () => {
    if (!analysisResult?.check_id) return;
    setIsEscalating(true);
    try {
      const caseRes = await quickCheckApi.escalate(analysisResult.check_id);
      navigate(`/cases/${caseRes.case_id}`);
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Failed to escalate quick check into a full investigation case.');
    } finally {
      setIsEscalating(false);
    }
  };

  const verdictStyles = {
    NO_OBVIOUS_TRACES: {
      badge: 'bg-emerald-50 text-emerald-800 border-emerald-300',
      title: 'NO OBVIOUS TRACES OF EDITING DETECTED',
      icon: <CheckCircle2 className="w-5 h-5 text-emerald-600" />,
    },
    SUSPICIOUS_TRACES_FOUND: {
      badge: 'bg-amber-50 text-amber-800 border-amber-300',
      title: 'SUSPICIOUS TRACES IDENTIFIED — MANUAL REVIEW RECOMMENDED',
      icon: <AlertTriangle className="w-5 h-5 text-amber-600" />,
    },
    STRONG_EVIDENCE_OF_EDITING: {
      badge: 'bg-rose-50 text-rose-800 border-rose-300',
      title: 'STRONG EVIDENCE OF DIGITAL ALTERATION FOUND',
      icon: <ShieldAlert className="w-5 h-5 text-rose-600" />,
    },
  };

  return (
    <div className="space-y-6 max-w-6xl mx-auto">
      {/* Header Banner */}
      <GlassCard className="p-6 bg-gradient-to-r from-amber-50 via-white to-slate-50 border-amber-200/80 shadow-xs">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div className="space-y-1">
            <div className="flex items-center gap-2">
              <span className="p-1.5 rounded-lg bg-amber-500 text-white shadow-xs">
                <Zap className="w-5 h-5" />
              </span>
              <span className="text-xs font-mono font-bold tracking-wider uppercase text-amber-700">
                Standalone Digital Forensics
              </span>
            </div>
            <h1 className="text-2xl font-bold tracking-tight text-slate-900">
              Quick Check Tool
            </h1>
            <p className="text-xs text-slate-600 max-w-2xl leading-relaxed">
              Instantly inspect arbitrary files (JPG, PNG, WEBP, TIFF, PDF, DOCX) for traces of digital tampering, compression anomalies, multiple PDF revisions, or tracked changes in Word documents.
            </p>
          </div>

          <div className="flex items-center gap-2">
            <span className="text-[10px] px-2.5 py-1 rounded-full bg-slate-100 text-slate-700 border border-slate-200 font-mono font-semibold">
              Supports: Images • PDF • DOCX
            </span>
          </div>
        </div>
      </GlassCard>

      {/* Honest Framing Alert Banner */}
      <div className="p-4 rounded-xl bg-blue-50 border border-blue-200 text-blue-900 flex items-start gap-3 text-xs leading-relaxed">
        <Info className="w-4 h-4 text-blue-600 shrink-0 mt-0.5" />
        <div>
          <span className="font-bold block text-blue-950 uppercase tracking-wider text-[10px] mb-0.5">
            Honest Forensic Scope & Limitations
          </span>
          This tool looks for common signs of digital editing (different compression levels, modified metadata, pasted elements, multiple PDF revisions, tracked changes in Word docs). <strong>It CANNOT prove an image or document is authentic.</strong> A clean result only means no obvious traces of editing were found.
        </div>
      </div>

      {/* Upload Zone */}
      {!analysisResult && (
        <GlassCard className="p-8">
          <div
            onDragOver={(e) => e.preventDefault()}
            onDrop={handleDrop}
            className="border-2 border-dashed border-slate-300 hover:border-blue-500 rounded-2xl p-8 text-center transition-colors flex flex-col items-center justify-center space-y-4 bg-slate-50/50 cursor-pointer"
            onClick={() => fileInputRef.current?.click()}
          >
            <input
              type="file"
              ref={fileInputRef}
              onChange={handleFileChange}
              accept=".jpg,.jpeg,.png,.webp,.tif,.tiff,.pdf,.docx"
              className="hidden"
            />
            <div className="w-12 h-12 rounded-2xl bg-blue-50 text-blue-600 flex items-center justify-center shadow-xs">
              <Upload className="w-6 h-6" />
            </div>
            <div>
              <p className="text-sm font-bold text-slate-800">
                {selectedFile ? selectedFile.name : 'Drop file here or click to browse'}
              </p>
              <p className="text-xs text-slate-500 mt-1">
                Supported formats: JPG, PNG, WEBP, TIFF, PDF, DOCX (Max 15MB)
              </p>
            </div>

            {selectedFile && (
              <div className="pt-2 flex items-center gap-3">
                <GlassButton
                  variant="primary"
                  size="md"
                  onClick={(e) => {
                    e.stopPropagation();
                    handleRunAnalysis();
                  }}
                  disabled={isAnalyzing}
                  icon={isAnalyzing ? <RefreshCw className="w-4 h-4 animate-spin" /> : <Zap className="w-4 h-4" />}
                >
                  {isAnalyzing ? 'Running Forensic Checks...' : 'Run Quick Check'}
                </GlassButton>
              </div>
            )}
          </div>

          {errorMessage && (
            <div className="mt-4 p-3 rounded-xl bg-red-50 border border-red-200 text-red-800 text-xs">
              {errorMessage}
            </div>
          )}
        </GlassCard>
      )}

      {/* Analysis Results View */}
      {analysisResult && (
        <div className="space-y-6">
          {/* Verdict Banner */}
          {(() => {
            const vStyle = verdictStyles[analysisResult.verdict as keyof typeof verdictStyles] || verdictStyles.SUSPICIOUS_TRACES_FOUND;
            return (
              <div className={`p-5 rounded-2xl border ${vStyle.badge} shadow-xs space-y-3`}>
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                  <div className="flex items-center gap-3">
                    <div className="p-2 rounded-xl bg-white/80 shadow-2xs">
                      {vStyle.icon}
                    </div>
                    <div>
                      <span className="text-[10px] font-mono uppercase font-bold tracking-wider opacity-70">
                        Quick Check Verdict // {analysisResult.file_type}
                      </span>
                      <h2 className="text-base font-bold tracking-tight">
                        {vStyle.title}
                      </h2>
                    </div>
                  </div>

                  <div className="flex items-center gap-2">
                    <GlassButton
                      size="sm"
                      variant="primary"
                      onClick={handleEscalateToCase}
                      disabled={isEscalating}
                      icon={<Briefcase className="w-4 h-4" />}
                    >
                      {isEscalating ? 'Opening Case...' : 'Create Full Case from This'}
                    </GlassButton>
                    <GlassButton
                      size="sm"
                      variant="secondary"
                      onClick={() => {
                        setSelectedFile(null);
                        setAnalysisResult(null);
                      }}
                      icon={<RefreshCw className="w-4 h-4" />}
                    >
                      Check Another File
                    </GlassButton>
                  </div>
                </div>

                <p className="text-xs leading-relaxed font-medium pt-1 border-t border-black/10">
                  {analysisResult.summary}
                </p>
              </div>
            );
          })()}

          {/* Visual Evidence (ELA Heatmap for Images) */}
          {analysisResult.visual_evidence_b64 && (
            <GlassCard className="p-6 space-y-4">
              <div className="flex items-center justify-between border-b border-slate-200 pb-3">
                <div className="flex items-center gap-2">
                  <Layers className="w-4 h-4 text-blue-600" />
                  <h3 className="text-sm font-bold text-slate-900">
                    Error Level Analysis (ELA) Compression Heatmap
                  </h3>
                </div>
                <div className="flex items-center gap-2">
                  <button
                    type="button"
                    onClick={() => setActiveLayer(activeLayer === 'ela' ? 'original' : 'ela')}
                    className="text-xs px-2.5 py-1 rounded-lg border border-slate-300 bg-white font-medium hover:bg-slate-50"
                  >
                    {activeLayer === 'ela' ? 'View Original File' : 'View ELA Heatmap'}
                  </button>
                </div>
              </div>

              <div className="relative rounded-xl border border-slate-200 bg-slate-950 flex items-center justify-center p-2 overflow-hidden max-h-[420px]">
                <img
                  src={activeLayer === 'ela' ? analysisResult.visual_evidence_b64 : (selectedFile ? URL.createObjectURL(selectedFile) : '')}
                  alt="Forensic Evidence"
                  className="max-h-[400px] w-auto object-contain rounded"
                />
              </div>
              <p className="text-[11px] text-slate-500 italic">
                Brighter colored clusters on the ELA heatmap indicate sections with anomalous JPEG compression rates, characteristic of copied, pasted, or retouched content.
              </p>
            </GlassCard>
          )}

          {/* Metadata Timeline (PDF / DOCX / EXIF) */}
          {analysisResult.metadata_timeline && analysisResult.metadata_timeline.length > 0 && (
            <GlassCard className="p-6 space-y-4">
              <div className="flex items-center gap-2 border-b border-slate-200 pb-3">
                <Clock className="w-4 h-4 text-indigo-600" />
                <h3 className="text-sm font-bold text-slate-900">
                  Document History & Metadata Timeline
                </h3>
              </div>

              <div className="space-y-3">
                {analysisResult.metadata_timeline.map((event: any, idx: number) => (
                  <div key={idx} className="flex items-start gap-3 p-3 rounded-xl bg-slate-50 border border-slate-200 text-xs">
                    <div className="w-2 h-2 rounded-full bg-blue-600 mt-1.5 shrink-0" />
                    <div className="flex-1 space-y-0.5">
                      <div className="flex items-center justify-between">
                        <span className="font-bold text-slate-900">{event.event}</span>
                        <span className="font-mono text-slate-500 text-[11px]">{event.time}</span>
                      </div>
                      {event.software && (
                        <p className="text-[11px] text-slate-600 font-mono">
                          Software / Author: <span className="font-bold text-slate-800">{event.software}</span>
                        </p>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </GlassCard>
          )}

          {/* Evidence Finding Cards */}
          <div className="space-y-3">
            <h3 className="text-sm font-bold text-slate-900">
              Detailed Evidence Findings ({analysisResult.findings?.length || 0})
            </h3>
            {analysisResult.findings?.map((finding: any) => (
              <FindingCard
                key={finding.id}
                finding={{
                  ...finding,
                  confidence: 0.95,
                  technicalDetails: finding.technical,
                }}
              />
            ))}
          </div>
        </div>
      )}
    </div>
  );
};
