import React from 'react';
import { useNavigate } from 'react-router-dom';
import { X, BookOpen, HelpCircle, CheckCircle2 } from 'lucide-react';
import { usePreferences } from '../../context/PreferencesContext';
import { GlassButton } from '../glass/GlassButton';

export const HELP_TOPICS: Record<string, { title: string; content: string; tips: string[] }> = {
  quality: {
    title: 'Image Quality & Optical Preprocessing',
    content: 'Before attempting OCR or forensic checks, VERISIGHT evaluates document clarity. Blurry photos, heavy flash glare, or skewed angles lead to false positive fraud alerts.',
    tips: [
      'Sharpness (Laplacian >= 100): If below 100, retake photo in bright natural light.',
      'Glare Detection: Turn off phone flash to avoid white hot spots over text.',
      'Auto-Deskew: VERISIGHT automatically rotates tilted documents up to 45 degrees.',
    ],
  },
  ocr: {
    title: 'OCR Extraction & Field Bounding Boxes',
    content: 'PaddleOCR scans the document image to identify text fields (Name, Date of Birth, Expiration, Document Number) and places visual bounding boxes around them.',
    tips: [
      'Confidence Scores: Green indicates >90% OCR confidence. Amber fields should be manually checked against the image.',
      'Field Correction: Security officers can click any field to edit mistakes before saving.',
    ],
  },
  mrz: {
    title: 'Machine Readable Zone (MRZ) Verification',
    content: 'Official ICAO Doc 9303 passports and visas print 2 or 3 lines of coded data at the bottom. These lines include mathematical check digits that lock the document number, DOB, and expiry date.',
    tips: [
      'Check Digits: Every number is multiplied by weights [7, 3, 1] modulo 10.',
      'If MRZ fails: A mismatch strongly suggests altered text or an expired forged date.',
    ],
  },
  forensics: {
    title: 'Multi-Factor Forensic Laboratory',
    content: 'VERISIGHT runs 5 independent digital forensics checks without requiring external internet or government databases.',
    tips: [
      'Error Level Analysis (ELA): Highlights sections saved at different JPEG compression levels (signs of copy-pasting).',
      'EXIF Metadata: Checks if editing software (Photoshop, GIMP) was saved in the file tags.',
      'Texture Analysis: Detects mismatched grain or surface discontinuities.',
      'Font & Alignment: Verifies that characters lie on a consistent typographic baseline.',
      'Portrait Replacement: Checks boundary artifacts around the traveler photo.',
    ],
  },
  face: {
    title: 'Biometric Face Verification & DPDP Act 2023',
    content: 'Compares the document photo with a live webcam snapshot. Under Section 6 of the Digital Personal Data Protection Act 2023, explicit consent is required before processing facial biometrics.',
    tips: [
      'Ephemeral Processing: Face embeddings are discarded immediately after comparison.',
      'Match Threshold: >=75% indicates high confidence match.',
      'No Storage: No face vectors or photos are saved to external databases.',
    ],
  },
  risk: {
    title: 'Explainable Multi-Layer Risk Engine',
    content: 'Rules from all engines are compiled using transparent, deterministic scoring. No black-box AI scores.',
    tips: [
      'CLEAR: No critical anomalies detected across tested factors.',
      'REVIEW: Low quality or minor discrepancies require human review.',
      'HIGH RISK: Critical check digit failure or forensic tampering found.',
      'Human Oversight: Officers can formally override decisions with recorded justification.',
    ],
  },
  cases: {
    title: 'Investigation Cases & Chain of Custody',
    content: 'When suspicious documents are flagged, security officers open an Investigation Case to attach notes, interview logs, and close the case with mandatory justification.',
    tips: [
      'Notes: Every note is stamped with the officer badge number and timestamp.',
      'Audit Lock: All state changes are written to the cryptographic SHA-256 hash ledger.',
    ],
  },
};

export const HelpDrawer: React.FC = () => {
  const { isHelpOpen, closeHelp, helpTopic } = usePreferences();
  const navigate = useNavigate();

  if (!isHelpOpen) return null;

  const topicData = (helpTopic && HELP_TOPICS[helpTopic]) || {
    title: 'VERISIGHT Officer Guidance',
    content: 'VERISIGHT helps security officers inspect travel and identity credentials using automated computer vision and digital forensics.',
    tips: [
      'Remember: This is a screening aid. A human officer always makes the final border decision.',
      'Use the 6-step verification story on top of every page to track progress.',
      'Toggle Simple Mode / Expert Mode in the topbar to adjust detail levels.',
    ],
  };

  return (
    <div className="fixed inset-0 z-50 overflow-hidden flex justify-end">
      {/* Backdrop */}
      <div
        className="fixed inset-0 bg-slate-950/40 backdrop-blur-xs transition-opacity"
        onClick={closeHelp}
      />

      {/* Drawer Panel */}
      <div className="relative w-full max-w-md bg-white h-full shadow-2xl border-l border-slate-200 p-6 flex flex-col justify-between z-10 overflow-y-auto">
        <div className="space-y-5">
          {/* Header */}
          <div className="flex items-center justify-between border-b border-slate-100 pb-3">
            <div className="flex items-center gap-2">
              <span className="p-1.5 rounded-lg bg-blue-100 text-blue-700">
                <HelpCircle className="w-5 h-5" />
              </span>
              <div>
                <span className="text-[10px] font-mono uppercase tracking-wider text-blue-600 font-bold block">
                  Officer Field Guide
                </span>
                <h3 className="text-base font-bold text-slate-900">
                  {topicData.title}
                </h3>
              </div>
            </div>
            <button
              type="button"
              onClick={closeHelp}
              className="p-1 rounded-lg hover:bg-slate-100 text-slate-400 hover:text-slate-700"
            >
              <X className="w-5 h-5" />
            </button>
          </div>

          {/* Body */}
          <div className="space-y-3 text-xs text-slate-700 leading-relaxed">
            <p className="font-medium bg-slate-50 p-3 rounded-xl border border-slate-100">
              {topicData.content}
            </p>

            <div className="space-y-2 pt-2">
              <span className="text-[11px] font-bold text-slate-900 uppercase tracking-wider block">
                Key Verification Tips:
              </span>
              <ul className="space-y-2">
                {topicData.tips.map((tip, idx) => (
                  <li key={idx} className="flex items-start gap-2 bg-blue-50/50 p-2.5 rounded-lg border border-blue-100/60 text-slate-800">
                    <CheckCircle2 className="w-4 h-4 text-blue-600 shrink-0 mt-0.5" />
                    <span>{tip}</span>
                  </li>
                ))}
              </ul>
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="pt-4 border-t border-slate-100 flex items-center justify-between gap-3">
          <GlassButton
            size="sm"
            variant="secondary"
            onClick={() => {
              closeHelp();
              navigate('/help');
            }}
            icon={<BookOpen className="w-4 h-4" />}
          >
            Open Full Help Center
          </GlassButton>
          <GlassButton
            size="sm"
            variant="ghost"
            onClick={closeHelp}
          >
            Close Guide
          </GlassButton>
        </div>
      </div>
    </div>
  );
};
