import React, { useState } from 'react';
import { Info } from 'lucide-react';
import { usePreferences } from '../../context/PreferencesContext';

export interface GlossaryDefinition {
  term: string;
  plain: string;
  technical: string;
}

export const GLOSSARY: Record<string, GlossaryDefinition> = {
  OCR: {
    term: 'Optical Character Recognition (OCR)',
    plain: 'Computer vision that reads printed letters and numbers from a photo into machine-editable text.',
    technical: 'PaddleOCR / Tesseract neural text detection and recognition model.',
  },
  MRZ: {
    term: 'Machine Readable Zone (MRZ)',
    plain: 'The 2 or 3 lines of special coded letters and chevrons (<<<) printed at the bottom of passports and visas.',
    technical: 'ICAO Doc 9303 standard layout (TD1, TD2, TD3) with optical character encoding.',
  },
  ELA: {
    term: 'Error Level Analysis (ELA)',
    plain: 'A check that reveals if a section of a picture was pasted in or edited after the photo was taken.',
    technical: 'Analyzes differences in JPEG compression error rates across 8x8 DCT quantization grids.',
  },
  'Check Digit': {
    term: 'Check Digit (Checksum)',
    plain: 'A security number printed in the passport code calculated from dates and numbers to prove they were not changed.',
    technical: 'Modulo-10 cyclical weighting algorithm [7, 3, 1] defined by ICAO 9303.',
  },
  Heatmap: {
    term: 'Forensic Heatmap',
    plain: 'A color overlay highlighting suspicious areas in bright colors (red/yellow) where tampering was detected.',
    technical: 'Pixel-level spatial variance map normalized across 0-255 RGB channels.',
  },
  'Laplacian Variance': {
    term: 'Sharpness Score (Laplacian Variance)',
    plain: 'A mathematical measure of how focused or blurry a photo is.',
    technical: 'Variance of the Laplacian operator (cv2.Laplacian) applied to grayscale image; score >= 100 indicates readable clarity.',
  },
  SSIM: {
    term: 'Structural Similarity (SSIM)',
    plain: 'Compares the texture of two images or sections to see if they share the same lighting and grain.',
    technical: 'Evaluates luminance, contrast, and structural degradation between reference and sample patches.',
  },
  'Hash Chain': {
    term: 'Cryptographic Hash Chain',
    plain: 'A digital ledger where each action is permanently sealed with a tamper-proof digital fingerprint.',
    technical: 'Merkle-style linked SHA-256 blocks where every record includes the cryptographic hash of the prior block.',
  },
  Confidence: {
    term: 'Extraction Confidence',
    plain: 'How sure the system is that the computer correctly read the printed text.',
    technical: 'Softmax probability score computed by the deep learning recognition head for each character.',
  },
  Metadata: {
    term: 'EXIF Metadata',
    plain: 'Hidden background information saved inside the file, such as camera model, editing software, and timestamps.',
    technical: 'Exchangeable Image File Format tags including Software, DateTimeOriginal, and ModifyDate.',
  },
  'DPDP Act': {
    term: 'Digital Personal Data Protection (DPDP) Act 2023',
    plain: 'Indian data privacy law requiring clear affirmative consent before processing personal identity and biometric data.',
    technical: 'DPDP Act 2023 §6 compliant ephemeral face verification; zero persistent biometric template storage.',
  },
};

interface GlossaryTooltipProps {
  term: keyof typeof GLOSSARY | string;
  children?: React.ReactNode;
}

export const GlossaryTooltip: React.FC<GlossaryTooltipProps> = ({ term, children }) => {
  const [isOpen, setIsOpen] = useState(false);
  const { mode } = usePreferences();
  const definition = GLOSSARY[term] || {
    term: term,
    plain: 'Security screening term used in document verification.',
    technical: 'Automated verification metric.',
  };

  return (
    <span className="relative inline-flex items-center gap-1 group">
      <span className="border-b border-dotted border-blue-400 text-slate-800 cursor-help font-medium">
        {children || term}
      </span>
      <button
        type="button"
        onClick={() => setIsOpen(!isOpen)}
        onMouseEnter={() => setIsOpen(true)}
        onMouseLeave={() => setIsOpen(false)}
        className="text-slate-400 hover:text-blue-600 transition-colors inline-flex items-center"
        aria-label={`Glossary explanation for ${term}`}
      >
        <Info className="w-3.5 h-3.5 inline" />
      </button>

      {isOpen && (
        <div className="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 w-72 p-3 bg-slate-900/95 text-slate-100 rounded-xl shadow-xl backdrop-blur-md border border-slate-700 text-xs z-50 pointer-events-none">
          <p className="font-bold text-sky-400 mb-1 flex items-center justify-between">
            <span>{definition.term}</span>
          </p>
          <p className="text-slate-200 leading-relaxed text-[11px] mb-1.5">
            {definition.plain}
          </p>
          {mode === 'expert' && (
            <p className="text-[10px] font-mono text-slate-400 pt-1.5 border-t border-slate-700">
              <span className="text-amber-400 font-semibold">Technical:</span> {definition.technical}
            </p>
          )}
          <div className="absolute top-full left-1/2 -translate-x-1/2 border-4 border-transparent border-t-slate-900/95" />
        </div>
      )}
    </span>
  );
};
