import React, { useState, useEffect, useRef } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import {
  UserCheck, ShieldCheck, Camera, Upload, AlertTriangle, ArrowRight,
  ArrowLeft, CheckCircle2, XCircle, RefreshCw, Eye, Lock
} from 'lucide-react';
import { GlassCard } from '../components/glass/GlassCard';
import { GlassButton } from '../components/glass/GlassButton';
import { EmptyState } from '../components/common/EmptyState';
import { LoadingSkeleton } from '../components/common/LoadingSkeleton';
import { screeningsApi, faceApi } from '../services/api';
import type { Screening } from '../types';

interface FaceQuality {
  is_acceptable: boolean;
  blur_score: number;
  mean_luminance: number;
  resolution: [number, number];
  flags: string[];
}

interface FaceVerifyResult {
  similarity_score: number;
  similarity_percentage: number;
  threshold: number;
  is_match: boolean;
  confidence_band: 'HIGH' | 'MEDIUM' | 'LOW';
  doc_quality: FaceQuality;
  live_quality: FaceQuality;
  caveats: string[];
  disclaimer: string;
  privacy_notice: string;
}

export const FaceVerificationPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();

  const [screening, setScreening] = useState<Screening | null>(null);
  const [docPortraitB64, setDocPortraitB64] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Consent state
  const [consentGranted, setConsentGranted] = useState(false);

  // Live capture mode: 'camera' | 'upload'
  const [captureMode, setCaptureMode] = useState<'camera' | 'upload'>('upload');
  const [capturedBlob, setCapturedBlob] = useState<Blob | null>(null);
  const [capturedPreview, setCapturedPreview] = useState<string | null>(null);
  const [isCameraActive, setIsCameraActive] = useState(false);

  // Verification execution
  const [isVerifying, setIsVerifying] = useState(false);
  const [verifyResult, setVerifyResult] = useState<FaceVerifyResult | null>(null);

  const videoRef = useRef<HTMLVideoElement>(null);
  const streamRef = useRef<MediaStream | null>(null);

  useEffect(() => {
    if (!id) return;
    const loadData = async () => {
      setIsLoading(true);
      setError(null);
      try {
        const [screenData, portraitData] = await Promise.all([
          screeningsApi.get(id),
          faceApi.getPortrait(id),
        ]);
        setScreening(screenData);
        setDocPortraitB64(portraitData.portrait_b64);
      } catch (err: any) {
        setError(err.response?.data?.detail || 'Failed to initialize face verification module.');
      } finally {
        setIsLoading(false);
      }
    };
    loadData();

    return () => {
      stopCamera();
    };
  }, [id]);

  const startCamera = async () => {
    setError(null);
    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        video: { width: 640, height: 480, facingMode: 'user' },
      });
      streamRef.current = stream;
      if (videoRef.current) {
        videoRef.current.srcObject = stream;
        videoRef.current.play();
      }
      setIsCameraActive(true);
      setCaptureMode('camera');
    } catch (err) {
      setError('Webcam feed could not be accessed. Please upload a live portrait photo manually.');
      setIsCameraActive(false);
    }
  };

  const stopCamera = () => {
    if (streamRef.current) {
      streamRef.current.getTracks().forEach((track) => track.stop());
      streamRef.current = null;
    }
    setIsCameraActive(false);
  };

  const captureFrame = () => {
    if (!videoRef.current) return;
    const canvas = document.createElement('canvas');
    canvas.width = videoRef.current.videoWidth || 640;
    canvas.height = videoRef.current.videoHeight || 480;
    const ctx = canvas.getContext('2d');
    if (ctx) {
      ctx.drawImage(videoRef.current, 0, 0, canvas.width, canvas.height);
      canvas.toBlob((blob) => {
        if (blob) {
          setCapturedBlob(blob);
          setCapturedPreview(canvas.toDataURL('image/jpeg'));
          stopCamera();
        }
      }, 'image/jpeg', 0.9);
    }
  };

  const handleFileUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      setCapturedBlob(file);
      const reader = new FileReader();
      reader.onloadend = () => {
        setCapturedPreview(reader.result as string);
      };
      reader.readAsDataURL(file);
    }
  };

  const executeVerification = async () => {
    if (!id || !capturedBlob || !consentGranted) return;
    setIsVerifying(true);
    setError(null);

    const formData = new FormData();
    formData.append('consent_granted', 'true');
    formData.append('live_image', capturedBlob, 'live_face.jpg');

    try {
      const data = await faceApi.verify(id, formData);
      setVerifyResult(data);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Biometric matching calculation encountered an error.');
    } finally {
      setIsVerifying(false);
    }
  };

  if (isLoading) {
    return (
      <div className="space-y-6">
        <LoadingSkeleton className="h-28" />
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <LoadingSkeleton className="h-96" />
          <LoadingSkeleton className="h-96" />
        </div>
      </div>
    );
  }

  if (error && !docPortraitB64) {
    return (
      <EmptyState
        icon={<AlertTriangle className="w-8 h-8" />}
        title="Biometric Module Inaccessible"
        description={error}
        actionText="Return to Forensics Lab"
        onAction={() => navigate(`/screenings/${id}/forensics`)}
      />
    );
  }

  return (
    <div className="space-y-6 max-w-7xl mx-auto pb-12">
      {/* Top Header & Navigation Stepper */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-200/80 pb-4">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="text-xs font-semibold px-2.5 py-0.5 rounded-full bg-blue-50 text-blue-700 border border-blue-200 font-mono">
              STEP 7 / OPTIONAL
            </span>
            <span className="text-xs text-slate-500 font-mono">REF: {screening?.reference_no}</span>
          </div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-900 flex items-center gap-2">
            <UserCheck className="w-6 h-6 text-blue-600" />
            Biometric Face Verification
          </h1>
          <p className="text-sm text-slate-600">
            Ephemeral facial comparison between extracted document portrait and live subject capture.
          </p>
        </div>

        {/* Workflow Stepper Controls */}
        <div className="flex items-center gap-3">
          <Link to={`/screenings/${id}/forensics`}>
            <GlassButton variant="secondary" size="sm" className="gap-2">
              <ArrowLeft className="w-4 h-4" />
              Forensics
            </GlassButton>
          </Link>
          <Link to={`/screenings/${id}/risk`}>
            <GlassButton variant="primary" size="sm" className="gap-2">
              Continue to Risk Engine
              <ArrowRight className="w-4 h-4" />
            </GlassButton>
          </Link>
        </div>
      </div>

      {/* DPDP Act Statutory Consent Gate */}
      <GlassCard className="p-5 border-l-4 border-l-blue-600 bg-blue-50/40">
        <div className="flex items-start gap-4">
          <div className="p-2 rounded-lg bg-blue-100/80 text-blue-700 shrink-0">
            <Lock className="w-5 h-5" />
          </div>
          <div className="space-y-2 flex-1">
            <div className="flex items-center justify-between">
              <h3 className="text-sm font-semibold text-slate-900">
                Statutory Biometric Consent Gate (DPDP Act 2023 §6)
              </h3>
              <span className="text-xs font-mono px-2 py-0.5 rounded bg-emerald-50 text-emerald-700 border border-emerald-200">
                EPHEMERAL RAM RETENTION
              </span>
            </div>
            <p className="text-xs text-slate-600 leading-relaxed">
              Biometric verification is strictly voluntary and requires explicit informed subject authorization.
              Raw camera captures and intermediate visual embeddings are processed in volatile RAM and permanently
              purged upon similarity score computation. No facial artifacts are written to long-term storage or database.
            </p>
            <label className="flex items-center gap-3 pt-2 cursor-pointer select-none">
              <input
                type="checkbox"
                checked={consentGranted}
                onChange={(e) => setConsentGranted(e.target.checked)}
                className="w-4 h-4 rounded border-slate-300 text-blue-600 focus:ring-blue-500"
              />
              <span className="text-xs font-medium text-slate-800">
                Subject has provided affirmative consent for one-time ephemeral identity comparison.
              </span>
            </label>
          </div>
        </div>
      </GlassCard>

      {/* Dual Comparison Stage */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Left Column: Document Extracted Portrait */}
        <GlassCard className="p-5 space-y-4">
          <div className="flex items-center justify-between border-b border-slate-200/80 pb-3">
            <div className="flex items-center gap-2">
              <Eye className="w-4 h-4 text-blue-600" />
              <h2 className="text-sm font-semibold text-slate-900">Extracted Document Portrait</h2>
            </div>
            <span className="text-xs font-mono text-slate-500">ICAO TD3 Photo Window</span>
          </div>

          <div className="flex flex-col items-center justify-center p-4 bg-slate-100/80 rounded-xl min-h-[320px]">
            {docPortraitB64 ? (
              <div className="space-y-3 text-center">
                <img
                  src={docPortraitB64}
                  alt="Extracted Document Portrait"
                  className="w-48 h-56 object-cover rounded-lg border-2 border-slate-300 shadow-sm mx-auto"
                />
                <span className="inline-block text-xs font-mono text-slate-600 bg-white/80 px-2 py-1 rounded border border-slate-200">
                  Rectified Crop: 128 x 128 Normalized
                </span>
              </div>
            ) : (
              <div className="text-center text-slate-500 text-xs">
                Document portrait zone could not be localized.
              </div>
            )}
          </div>

          <div className="text-xs text-slate-500 flex items-center gap-1.5">
            <ShieldCheck className="w-3.5 h-3.5 text-emerald-600 shrink-0" />
            <span>Extracted automatically from preprocessed document evidence.</span>
          </div>
        </GlassCard>

        {/* Right Column: Live Subject Capture */}
        <GlassCard className="p-5 space-y-4">
          <div className="flex items-center justify-between border-b border-slate-200/80 pb-3">
            <div className="flex items-center gap-2">
              <Camera className="w-4 h-4 text-blue-600" />
              <h2 className="text-sm font-semibold text-slate-900">Live Subject Capture</h2>
            </div>
            <div className="flex items-center gap-1">
              <button
                type="button"
                onClick={() => {
                  stopCamera();
                  setCaptureMode('upload');
                }}
                className={`text-xs px-2.5 py-1 rounded font-medium transition-colors ${
                  captureMode === 'upload'
                    ? 'bg-blue-600 text-white'
                    : 'text-slate-600 hover:bg-slate-100'
                }`}
              >
                Upload Photo
              </button>
              <button
                type="button"
                onClick={startCamera}
                className={`text-xs px-2.5 py-1 rounded font-medium transition-colors ${
                  captureMode === 'camera'
                    ? 'bg-blue-600 text-white'
                    : 'text-slate-600 hover:bg-slate-100'
                }`}
              >
                Webcam
              </button>
            </div>
          </div>

          <div className="flex flex-col items-center justify-center p-4 bg-slate-100/80 rounded-xl min-h-[320px] relative">
            {isCameraActive ? (
              <div className="space-y-3 w-full flex flex-col items-center">
                <video
                  ref={videoRef}
                  autoPlay
                  playsInline
                  className="w-full max-w-xs h-56 object-cover rounded-lg border-2 border-blue-500 shadow-sm"
                />
                <GlassButton variant="primary" size="sm" onClick={captureFrame} className="gap-2">
                  <Camera className="w-4 h-4" />
                  Capture Photo
                </GlassButton>
              </div>
            ) : capturedPreview ? (
              <div className="space-y-3 text-center">
                <img
                  src={capturedPreview}
                  alt="Captured Live Face"
                  className="w-48 h-56 object-cover rounded-lg border-2 border-emerald-500 shadow-sm mx-auto"
                />
                <div className="flex items-center justify-center gap-2">
                  <GlassButton
                    variant="secondary"
                    size="sm"
                    onClick={() => {
                      setCapturedBlob(null);
                      setCapturedPreview(null);
                      setVerifyResult(null);
                    }}
                    className="gap-1.5 text-xs"
                  >
                    <RefreshCw className="w-3.5 h-3.5" />
                    Clear / Retake
                  </GlassButton>
                </div>
              </div>
            ) : (
              <div className="text-center space-y-3 p-6">
                <div className="w-12 h-12 rounded-full bg-slate-200/80 flex items-center justify-center mx-auto text-slate-500">
                  <Upload className="w-6 h-6" />
                </div>
                <div className="space-y-1">
                  <p className="text-xs font-semibold text-slate-800">
                    Upload live reference photo or activate webcam
                  </p>
                  <p className="text-[11px] text-slate-500">
                    Supported: JPEG or PNG under 10MB
                  </p>
                </div>
                <label className="inline-block cursor-pointer">
                  <input
                    type="file"
                    accept="image/jpeg,image/png"
                    onChange={handleFileUpload}
                    className="hidden"
                  />
                  <span className="inline-flex items-center gap-2 px-3 py-1.5 rounded-lg text-xs font-medium bg-blue-600 text-white hover:bg-blue-700 transition-colors">
                    <Upload className="w-3.5 h-3.5" />
                    Select Live File
                  </span>
                </label>
              </div>
            )}
          </div>

          {/* Action Trigger */}
          <div className="flex items-center justify-between pt-2">
            <span className="text-xs text-slate-500">
              Requires consent confirmation above.
            </span>
            <GlassButton
              variant="primary"
              size="sm"
              disabled={!capturedBlob || !consentGranted || isVerifying}
              onClick={executeVerification}
              className="gap-2"
            >
              {isVerifying ? (
                <>
                  <RefreshCw className="w-4 h-4 animate-spin" />
                  Calculating Distance...
                </>
              ) : (
                <>
                  <UserCheck className="w-4 h-4" />
                  Execute Biometric Match
                </>
              )}
            </GlassButton>
          </div>
        </GlassCard>
      </div>

      {/* Verification Output Diagnostic Panel */}
      {verifyResult && (
        <GlassCard className="p-6 space-y-6 border-slate-200">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-200/80 pb-4">
            <div>
              <span className="text-xs font-mono text-slate-500">VERIFICATION ENGINE v1.2</span>
              <h2 className="text-lg font-bold text-slate-900 flex items-center gap-2">
                Biometric Cross-Check Results
              </h2>
            </div>
            <div className="flex items-center gap-2">
              {verifyResult.is_match ? (
                <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-emerald-50 text-emerald-700 border border-emerald-200">
                  <CheckCircle2 className="w-4 h-4 text-emerald-600" />
                  BIOMETRIC MATCH CONFIRMED
                </span>
              ) : (
                <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-amber-50 text-amber-700 border border-amber-200">
                  <XCircle className="w-4 h-4 text-amber-600" />
                  INCONCLUSIVE / DISSIMILAR
                </span>
              )}
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div className="p-4 bg-slate-50/80 rounded-xl border border-slate-200/60">
              <span className="text-xs text-slate-500 font-mono">SIMILARITY SCORE</span>
              <p className="text-2xl font-bold font-mono text-slate-900 mt-1">
                {verifyResult.similarity_percentage}%
              </p>
              <span className="text-[11px] text-slate-500">
                Cosine Metric: {verifyResult.similarity_score}
              </span>
            </div>

            <div className="p-4 bg-slate-50/80 rounded-xl border border-slate-200/60">
              <span className="text-xs text-slate-500 font-mono">PASS THRESHOLD</span>
              <p className="text-2xl font-bold font-mono text-slate-900 mt-1">
                {(verifyResult.threshold * 100).toFixed(1)}%
              </p>
              <span className="text-[11px] text-slate-500">Calibrated Boundary</span>
            </div>

            <div className="p-4 bg-slate-50/80 rounded-xl border border-slate-200/60">
              <span className="text-xs text-slate-500 font-mono">CONFIDENCE BAND</span>
              <p className="text-2xl font-bold text-slate-900 mt-1">
                {verifyResult.confidence_band}
              </p>
              <span className="text-[11px] text-slate-500">Feature Density</span>
            </div>

            <div className="p-4 bg-slate-50/80 rounded-xl border border-slate-200/60">
              <span className="text-xs text-slate-500 font-mono">OPTICAL QUALITY</span>
              <p className="text-2xl font-bold text-slate-900 mt-1">
                {verifyResult.doc_quality.is_acceptable && verifyResult.live_quality.is_acceptable
                  ? 'ACCEPTABLE'
                  : 'SUB-OPTIMAL'}
              </p>
              <span className="text-[11px] text-slate-500">Laplacian / Luminance Check</span>
            </div>
          </div>

          {/* Caveats & Statutory Disclaimer */}
          <div className="space-y-3 pt-2">
            <h4 className="text-xs font-semibold text-slate-800 uppercase tracking-wider">
              Algorithmic Limitations & Physical Caveats
            </h4>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
              {verifyResult.caveats.map((c, idx) => (
                <div key={idx} className="p-3 bg-slate-50 rounded-lg text-xs text-slate-600 border border-slate-200/60">
                  • {c}
                </div>
              ))}
            </div>

            <div className="p-3 bg-amber-50/60 rounded-lg border border-amber-200/60 text-xs text-amber-800 flex items-start gap-2.5">
              <AlertTriangle className="w-4 h-4 text-amber-600 shrink-0 mt-0.5" />
              <p className="leading-relaxed">
                <strong>Non-Conclusive Decision Support Notice:</strong> {verifyResult.disclaimer}
              </p>
            </div>
          </div>
        </GlassCard>
      )}

      {/* Bottom Navigation */}
      <div className="flex items-center justify-between pt-4 border-t border-slate-200/80">
        <Link to={`/screenings/${id}/forensics`}>
          <GlassButton variant="secondary" className="gap-2">
            <ArrowLeft className="w-4 h-4" />
            Back to Forensic Lab
          </GlassButton>
        </Link>
        <Link to={`/screenings/${id}/risk`}>
          <GlassButton variant="primary" className="gap-2">
            Continue to Risk Engine
            <ArrowRight className="w-4 h-4" />
          </GlassButton>
        </Link>
      </div>
    </div>
  );
};
