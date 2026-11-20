import React, { useState, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { 
  Upload, Camera, RefreshCw, FileText, CheckCircle2, 
  AlertTriangle, ShieldAlert, ArrowRight, X, Image as ImageIcon
} from 'lucide-react';
import { GlassCard } from '../components/glass/GlassCard';
import { GlassButton } from '../components/glass/GlassButton';
import { CaseStepper } from '../components/common/CaseStepper';
import { WhatNextPanel } from '../components/common/WhatNextPanel';
import { screeningsApi } from '../services/api';
import type { ScreeningStatusResponse } from '../types';

const DOCUMENT_TYPES = [
  { id: 'PASSPORT_TD3', label: 'Passport (ICAO TD3)', desc: 'Standard 2-line MRZ machine readable travel document' },
  { id: 'AADHAAR_CARD', label: 'Aadhaar Card (UIDAI / Non-MRZ)', desc: 'Indian National ID with 12-digit UID, photo, and address' },
  { id: 'PAN_CARD', label: 'PAN Card (Income Tax Dept / Non-MRZ)', desc: 'Indian Permanent Account Number tax identification card' },
  { id: 'ID_TD1', label: 'National ID Card (ICAO TD1)', desc: '3-line format identification card or driver license' },
  { id: 'VISA_TD2', label: 'Entry Visa Sticker (ICAO TD2)', desc: 'Diplomatic, employment or tourist visa sticker' },
];

const COMMON_COUNTRIES = [
  { code: 'IND', name: 'India (IND)' },
  { code: 'USA', name: 'United States (USA)' },
  { code: 'GBR', name: 'United Kingdom (GBR)' },
  { code: 'DEU', name: 'Germany (DEU)' },
  { code: 'FRA', name: 'France (FRA)' },
  { code: 'CAN', name: 'Canada (CAN)' },
  { code: 'AUS', name: 'Australia (AUS)' },
  { code: 'SGP', name: 'Singapore (SGP)' },
  { code: 'ARE', name: 'United Arab Emirates (ARE)' },
];

const SYNTHETIC_SCENARIOS = [
  { id: '', label: 'Real / Standard Ingestion' },
  { id: 'SCENARIO-1-CLEAN', label: 'Scenario 1: Clean Genuine Passport' },
  { id: 'SCENARIO-2-EXPIRED', label: 'Scenario 2: Expired Validity Passport' },
  { id: 'SCENARIO-3-MRZ-MISMATCH', label: 'Scenario 3: MRZ Check Digit & VIZ Mismatch' },
  { id: 'SCENARIO-4-TAMPERED-ELA', label: 'Scenario 4: Digitally Tampered Portrait / ELA Anomaly' },
  { id: 'SCENARIO-5-LOW-QUALITY', label: 'Scenario 5: Motion Blur & Specular Glare (Rescan Required)' },
];

export const NewScreeningPage: React.FC = () => {
  const navigate = useNavigate();
  const fileInputRef = useRef<HTMLInputElement>(null);
  const videoRef = useRef<HTMLVideoElement>(null);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [docType, setDocType] = useState('PASSPORT_TD3');
  const [countryCode, setCountryCode] = useState('IND');
  const [scenarioTag, setScenarioTag] = useState('');
  const [isSynthetic, setIsSynthetic] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [currentStep, setCurrentStep] = useState<string>('');
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  // Webcam state
  const [isCameraActive, setIsCameraActive] = useState(false);
  const [cameraStream, setCameraStream] = useState<MediaStream | null>(null);

  const handleFileSelect = (file: File) => {
    // Validation
    const validTypes = ['image/jpeg', 'image/png', 'image/jpg'];
    if (!validTypes.includes(file.type)) {
      setErrorMessage('Unsupported file format. Please upload JPEG or PNG identity document images.');
      return;
    }
    if (file.size > 15 * 1024 * 1024) {
      setErrorMessage('File size exceeds the 15 MB system boundary.');
      return;
    }

    setErrorMessage(null);
    setSelectedFile(file);
    const url = URL.createObjectURL(file);
    setPreviewUrl(url);
  };

  const onDragOver = (e: React.DragEvent) => {
    e.preventDefault();
  };

  const onDrop = (e: React.DragEvent) => {
    e.preventDefault();
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFileSelect(e.dataTransfer.files[0]);
    }
  };

  const startWebcam = async () => {
    setErrorMessage(null);
    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        video: { facingMode: 'environment', width: { ideal: 1920 }, height: { ideal: 1080 } },
      });
      setCameraStream(stream);
      setIsCameraActive(true);
      if (videoRef.current) {
        videoRef.current.srcObject = stream;
      }
    } catch (err) {
      setErrorMessage('Unable to access camera hardware. Verify browser permissions.');
    }
  };

  const stopWebcam = () => {
    if (cameraStream) {
      cameraStream.getTracks().forEach((track) => track.stop());
      setCameraStream(null);
    }
    setIsCameraActive(false);
  };

  const capturePhoto = () => {
    if (!videoRef.current) return;
    const canvas = document.createElement('canvas');
    canvas.width = videoRef.current.videoWidth || 1280;
    canvas.height = videoRef.current.videoHeight || 720;
    const ctx = canvas.getContext('2d');
    if (ctx) {
      ctx.drawImage(videoRef.current, 0, 0, canvas.width, canvas.height);
      canvas.toBlob((blob) => {
        if (blob) {
          const file = new File([blob], `scan_${Date.now()}.jpg`, { type: 'image/jpeg' });
          handleFileSelect(file);
          stopWebcam();
        }
      }, 'image/jpeg', 0.95);
    }
  };

  const clearSelection = () => {
    setSelectedFile(null);
    if (previewUrl) {
      URL.revokeObjectURL(previewUrl);
      setPreviewUrl(null);
    }
    setErrorMessage(null);
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  const handleSubmit = async (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    if (!selectedFile) {
      setErrorMessage('Please provide an identity document image to screen.');
      return;
    }

    setIsSubmitting(true);
    setErrorMessage(null);
    setUploadProgress(10);
    setCurrentStep('Hashing evidence & validating image headers...');

    try {
      const formData = new FormData();
      formData.append('file', selectedFile);
      formData.append('document_type', docType);
      formData.append('issuing_country_code', countryCode);
      formData.append('is_synthetic', String(isSynthetic || Boolean(scenarioTag)));
      formData.append('sync', 'false');
      if (scenarioTag) {
        formData.append('scenario_tag', scenarioTag);
      }

      const result = await screeningsApi.create(formData);
      const screeningId = result.id;
      setUploadProgress(15);
      setCurrentStep('Ingested & hashed evidence. Initializing screening pipeline...');

      const stageLabels: Record<string, string> = {
        QUALITY_ASSESSMENT: 'Evaluating optical sharpness, glare & resolution standards...',
        PREPROCESSING: 'Rectifying orientation, deskewing & bilateral denoising...',
        OCR_EXTRACTION: 'Running neural OCR & detecting character coordinates...',
        MRZ_PARSING: 'Parsing ICAO 9303 machine-readable travel zones...',
        VALIDATION_CROSSCHECK: 'Verifying check digits & cross-referencing fields...',
        FORENSICS_ANALYSIS: 'Executing 5-pillar digital forensics & ELA inspection...',
        RISK_SCORING: 'Computing risk rules & cryptographic Merkle block seal...',
        COMPLETED: 'Screening complete! Redirecting to Quality Report...',
      };

      // Poll real stage progress
      const pollInterval = setInterval(async () => {
        try {
          const statusData: ScreeningStatusResponse = await screeningsApi.getStatus(screeningId);
          
          if (statusData.overall_progress > 0) {
            setUploadProgress(Math.max(15, statusData.overall_progress));
          }
          if (statusData.current_stage && stageLabels[statusData.current_stage]) {
            setCurrentStep(stageLabels[statusData.current_stage]);
          }

          if (statusData.status === 'COMPLETED') {
            clearInterval(pollInterval);
            setUploadProgress(100);
            setCurrentStep('Screening complete! Redirecting to Quality Report...');
            setTimeout(() => {
              navigate(`/screenings/${screeningId}/quality`);
            }, 600);
          } else if (statusData.status === 'REJECTED_POOR_QUALITY') {
            clearInterval(pollInterval);
            setIsSubmitting(false);
            setUploadProgress(0);
            setErrorMessage(statusData.rescan_instructions || 'Document image does not meet optical quality criteria. Please rescan.');
          } else if (statusData.status === 'FAILED' || statusData.status === 'ABORTED') {
            clearInterval(pollInterval);
            setIsSubmitting(false);
            setUploadProgress(0);
            setErrorMessage(statusData.error_message || 'Screening pipeline encountered an error. Please retry.');
          }
        } catch (pollErr: any) {
          // Continue polling on transient network hiccup
        }
      }, 700);

    } catch (err: any) {
      setIsSubmitting(false);
      setUploadProgress(0);
      const detail = err.response?.data?.detail || err.message || 'An error occurred during document intake.';
      setErrorMessage(detail);
    }
  };

  return (
    <div className="space-y-6 max-w-6xl mx-auto">
      {/* 6-Step Case Stepper */}
      <CaseStepper currentStep={1} />

      {/* Recommended Next Action */}
      <WhatNextPanel
        recommendation="Select document category and provide an identity credential image."
        reason="The automated pipeline requires a clear image to evaluate resolution, sharpness, and ICAO 9303 compliance."
        actionText={selectedFile ? "Initiate Automated Pipeline" : "Choose File or Take Photo"}
        onAction={() => {
          if (selectedFile) {
            handleSubmit();
          } else if (fileInputRef.current) {
            fileInputRef.current.click();
          }
        }}
        helpTopic="quality"
      />

      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-2 border-b border-slate-200">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-900">Document Intake & Screening</h1>
          <p className="text-sm text-slate-500 mt-1">
            Ingest travel identity credentials for automated biometric, optical, and cryptographic MRZ verification.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <span className="px-3 py-1 text-xs font-semibold rounded-full bg-blue-100 text-blue-800 border border-blue-200">
            ICAO Doc 9303 Compliant
          </span>
          <span className="px-3 py-1 text-xs font-semibold rounded-full bg-slate-100 text-slate-700 border border-slate-200">
            SHA-256 Chained
          </span>
        </div>
      </div>

      {errorMessage && (
        <div className="p-4 rounded-xl bg-red-50 border border-red-200 flex items-start gap-3 text-red-800 text-sm">
          <ShieldAlert className="w-5 h-5 flex-shrink-0 text-red-600 mt-0.5" />
          <div className="flex-1">
            <span className="font-semibold block">Intake Blocked</span>
            {errorMessage}
          </div>
          <button onClick={() => setErrorMessage(null)} className="text-red-600 hover:text-red-800">
            <X className="w-4 h-4" />
          </button>
        </div>
      )}

      <form onSubmit={handleSubmit} className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left 2 Cols: Ingestion & Upload Canvas */}
        <div className="lg:col-span-2 space-y-6">
          <GlassCard className="p-6">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-base font-semibold text-slate-900 flex items-center gap-2">
                <FileText className="w-4 h-4 text-blue-600" />
                Document Capture & Ingestion
              </h2>
              <div className="flex items-center gap-2">
                {!isCameraActive ? (
                  <GlassButton type="button" size="sm" onClick={startWebcam} icon={<Camera className="w-4 h-4" />}>
                    Webcam Capture
                  </GlassButton>
                ) : (
                  <GlassButton type="button" size="sm" variant="destructive" onClick={stopWebcam} icon={<X className="w-4 h-4" />}>
                    Close Camera
                  </GlassButton>
                )}
              </div>
            </div>

            {/* Webcam Live View */}
            {isCameraActive && (
              <div className="relative mb-6 rounded-xl overflow-hidden border border-slate-300 bg-black aspect-video flex items-center justify-center">
                <video ref={videoRef} autoPlay playsInline className="w-full h-full object-cover" />
                <div className="absolute inset-x-0 bottom-4 flex justify-center items-center gap-4">
                  <GlassButton type="button" size="md" variant="primary" onClick={capturePhoto} icon={<Camera className="w-5 h-5" />}>
                    Take Snapshot
                  </GlassButton>
                </div>
                <div className="absolute top-3 left-3 bg-black/60 px-3 py-1 rounded text-xs font-mono text-white backdrop-blur">
                  ALIGN DOCUMENT EDGES INSIDE FRAME
                </div>
              </div>
            )}

            {/* Drag & Drop Zone */}
            {!previewUrl ? (
              <div
                onDragOver={onDragOver}
                onDrop={onDrop}
                onClick={() => fileInputRef.current?.click()}
                className="border-2 border-dashed border-slate-300 hover:border-blue-500 rounded-2xl p-10 flex flex-col items-center justify-center text-center cursor-pointer transition-colors bg-slate-50/50 hover:bg-blue-50/30"
              >
                <input
                  ref={fileInputRef}
                  type="file"
                  accept="image/png,image/jpeg,image/jpg"
                  className="hidden"
                  onChange={(e) => e.target.files?.[0] && handleFileSelect(e.target.files[0])}
                />
                <div className="w-16 h-16 rounded-full bg-blue-100 flex items-center justify-center text-blue-600 mb-4 shadow-sm">
                  <Upload className="w-8 h-8" />
                </div>
                <span className="text-base font-semibold text-slate-800">
                  Drop high-resolution scan or click to browse
                </span>
                <p className="text-xs text-slate-500 mt-2 max-w-sm">
                  Standard travel documents, MRZ passports, or national IDs. Supported formats: PNG, JPEG (up to 15 MB).
                </p>
                <div className="mt-4 flex gap-4 text-xs font-medium text-slate-500">
                  <span className="flex items-center gap-1">
                    <CheckCircle2 className="w-3.5 h-3.5 text-green-600" /> Tamper-evident SHA-256
                  </span>
                  <span className="flex items-center gap-1">
                    <CheckCircle2 className="w-3.5 h-3.5 text-green-600" /> Zero cloud persistence
                  </span>
                </div>
              </div>
            ) : (
              /* Preview Area */
              <div className="relative rounded-2xl border border-slate-200 overflow-hidden bg-slate-900 group">
                <img
                  src={previewUrl}
                  alt="Document Preview"
                  className="w-full max-h-[420px] object-contain mx-auto"
                />
                <div className="absolute top-3 right-3 flex items-center gap-2">
                  <button
                    type="button"
                    onClick={clearSelection}
                    className="p-2 rounded-full bg-white/90 text-slate-700 hover:bg-white hover:text-red-600 shadow-sm transition"
                    title="Remove document"
                  >
                    <X className="w-4 h-4" />
                  </button>
                </div>
                <div className="absolute bottom-3 left-3 right-3 bg-white/90 backdrop-blur-md p-3 rounded-xl border border-white/40 flex items-center justify-between text-xs text-slate-700">
                  <div className="flex items-center gap-2">
                    <ImageIcon className="w-4 h-4 text-blue-600" />
                    <span className="font-semibold text-slate-900 truncate max-w-[200px] sm:max-w-xs">
                      {selectedFile?.name}
                    </span>
                    <span className="text-slate-500">
                      ({((selectedFile?.size || 0) / (1024 * 1024)).toFixed(2)} MB)
                    </span>
                  </div>
                  <span className="text-green-700 font-semibold bg-green-100 px-2.5 py-0.5 rounded-full">
                    Ready for Ingestion
                  </span>
                </div>
              </div>
            )}

            {/* Submission Progress Indicator */}
            {isSubmitting && (
              <div className="mt-6 p-4 rounded-xl bg-gradient-to-r from-blue-50/90 to-sky-50/90 border border-blue-200/80 shadow-xs space-y-3 animate-pulse">
                <div className="flex items-center justify-between text-xs font-medium text-blue-900">
                  <span className="flex items-center gap-2">
                    <RefreshCw className="w-3.5 h-3.5 animate-spin text-blue-600 flex-shrink-0" />
                    <span>{currentStep}</span>
                  </span>
                  <span className="font-mono font-bold text-blue-700 bg-blue-100/80 px-2 py-0.5 rounded-md">
                    {uploadProgress}%
                  </span>
                </div>
                <div className="w-full h-2.5 rounded-full bg-blue-200/70 overflow-hidden shadow-inner">
                  <div 
                    className="h-full bg-gradient-to-r from-blue-600 via-sky-500 to-blue-600 rounded-full transition-all duration-300 ease-out"
                    style={{ width: `${uploadProgress}%` }}
                  />
                </div>
              </div>
            )}
          </GlassCard>

          {/* Supported Templates Notice */}
          <div className="p-4 rounded-xl bg-amber-50/60 border border-amber-200 text-xs text-amber-900 flex items-start gap-3">
            <AlertTriangle className="w-4 h-4 text-amber-600 flex-shrink-0 mt-0.5" />
            <div>
              <span className="font-semibold block mb-0.5">Template Verification Boundary</span>
              This system executes deterministic structural and check-digit validation strictly against ICAO Doc 9303 TD1, TD2, and TD3 travel documents. Non-standard domestic ID cards without machine-readable zones will be assessed for optical quality and visual text extraction only.
            </div>
          </div>
        </div>

        {/* Right Col: Document Metadata & Parameters */}
        <div className="space-y-6">
          <GlassCard className="p-6 space-y-5">
            <h2 className="text-base font-semibold text-slate-900 border-b border-slate-200 pb-3">
              Screening Parameters
            </h2>

            {/* Document Type Selector */}
            <div className="space-y-2">
              <label className="text-xs font-semibold text-slate-700 block">
                Target Credential Specification
              </label>
              <div className="space-y-2">
                {DOCUMENT_TYPES.map((dt) => (
                  <label
                    key={dt.id}
                    className={`flex items-start gap-3 p-3 rounded-xl border text-xs cursor-pointer transition ${
                      docType === dt.id
                        ? 'border-blue-600 bg-blue-50/50 text-blue-950 font-medium'
                        : 'border-slate-200 hover:border-slate-300 text-slate-700 bg-white'
                    }`}
                  >
                    <input
                      type="radio"
                      name="document_type"
                      value={dt.id}
                      checked={docType === dt.id}
                      onChange={(e) => setDocType(e.target.value)}
                      className="mt-0.5 text-blue-600 focus:ring-blue-500"
                    />
                    <div>
                      <div className="font-semibold text-slate-900">{dt.label}</div>
                      <div className="text-slate-500 mt-0.5 leading-snug">{dt.desc}</div>
                    </div>
                  </label>
                ))}
              </div>
            </div>

            {/* Issuing Country */}
            <div>
              <label className="text-xs font-semibold text-slate-700 block mb-1.5">
                Issuing State Authority (ISO 3166-1 alpha-3)
              </label>
              <select
                value={countryCode}
                onChange={(e) => setCountryCode(e.target.value)}
                className="w-full px-3 py-2 text-sm rounded-xl border border-slate-200 bg-white text-slate-800 focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                {COMMON_COUNTRIES.map((c) => (
                  <option key={c.code} value={c.code}>
                    {c.name}
                  </option>
                ))}
              </select>
            </div>

            {/* Synthetic & Demo Scenario Tagging */}
            <div className="pt-2 border-t border-slate-200">
              <div className="flex items-center justify-between mb-2">
                <label className="text-xs font-semibold text-slate-700">
                  Evaluation Scenario (Demo / Jury Mode)
                </label>
                <span className="text-[10px] font-mono text-blue-700 bg-blue-100 px-2 py-0.5 rounded">
                  SIH 2026
                </span>
              </div>
              <select
                value={scenarioTag}
                onChange={(e) => {
                  setScenarioTag(e.target.value);
                  setIsSynthetic(Boolean(e.target.value));
                }}
                className="w-full px-3 py-2 text-xs rounded-xl border border-slate-200 bg-white text-slate-800 focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                {SYNTHETIC_SCENARIOS.map((s) => (
                  <option key={s.id} value={s.id}>
                    {s.label}
                  </option>
                ))}
              </select>
              <p className="text-[11px] text-slate-500 mt-1.5 leading-relaxed">
                Flags the screening as synthetic evaluation data in the audit ledger so it remains distinct from production records.
              </p>
            </div>

            {/* Submit Button */}
            <div className="pt-4 border-t border-slate-200">
              <GlassButton
                type="submit"
                variant="primary"
                size="lg"
                disabled={!selectedFile || isSubmitting}
                className="w-full justify-center"
                icon={<ArrowRight className="w-5 h-5" />}
              >
                {isSubmitting ? 'Executing Pipeline...' : 'Commence Full Screening'}
              </GlassButton>
            </div>
          </GlassCard>
        </div>
      </form>
    </div>
  );
};
