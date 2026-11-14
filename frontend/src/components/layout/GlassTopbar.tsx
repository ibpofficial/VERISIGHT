import React from 'react';
import { useLocation } from 'react-router-dom';
import { HelpCircle, Languages, Sliders } from 'lucide-react';
import { useAuth } from '../../context/AuthContext';
import { usePreferences } from '../../context/PreferencesContext';

export const GlassTopbar: React.FC = () => {
  const { user } = useAuth();
  const location = useLocation();
  const { mode, toggleMode, language, toggleLanguage, openHelp, t } = usePreferences();

  const getPageTitle = (path: string) => {
    if (path === '/dashboard') return 'Command Center & Operations Dashboard';
    if (path === '/quick-check') return 'Quick Check — Standalone Document Inspection';
    if (path === '/help') return 'Officer Knowledge Base & Training Center';
    if (path.startsWith('/screenings/new')) return 'Document Ingestion & Screening Setup';
    if (path.includes('/quality')) return 'Image Quality & Optical Preprocessing';
    if (path.includes('/extraction')) return 'OCR Extraction & Field Mapping';
    if (path.includes('/mrz')) return 'MRZ Cryptographic Verification Studio';
    if (path.includes('/forensics')) return 'Multi-Factor Forensic Laboratory';
    if (path.includes('/face')) return 'Biometric Facial Similarity Verification';
    if (path.includes('/risk')) return 'Explainable Multi-Layer Risk Assessment';
    if (path.includes('/report')) return 'Forensic Dossier & PDF Report Generation';
    if (path === '/cases') return 'Investigation Center — Case Queue';
    if (path.startsWith('/cases/')) return 'Case Investigation & Evidence Desk';
    if (path === '/audit') return 'Cryptographic Audit Trail (SHA-256 Hash Chain)';
    if (path === '/admin/users') return 'Officer & User Access Administration';
    if (path === '/admin/config') return 'System Configuration & Rule Calibration';
    if (path === '/admin/engine-status') return 'Forensic Engine Health & Latency Monitor';
    return 'Identity & Travel Document Screening';
  };

  const getActiveHelpTopic = (path: string) => {
    if (path.includes('/quality')) return 'quality';
    if (path.includes('/extraction')) return 'ocr';
    if (path.includes('/mrz')) return 'mrz';
    if (path.includes('/forensics')) return 'forensics';
    if (path.includes('/face')) return 'face';
    if (path.includes('/risk')) return 'risk';
    if (path.startsWith('/cases')) return 'cases';
    return undefined;
  };

  return (
    <header className="h-16 bg-white/80 backdrop-blur-md border-b border-slate-200/80 fixed top-0 right-0 left-64 z-20 px-6 flex items-center justify-between shadow-2xs select-none">
      {/* Breadcrumb & View Info */}
      <div className="flex items-center gap-3">
        <h2 className="text-sm font-semibold text-slate-800 tracking-tight">
          {getPageTitle(location.pathname)}
        </h2>
      </div>

      {/* Center/Right Status & Telemetry */}
      <div className="flex items-center gap-3">
        {/* Simple Mode / Expert Mode Toggle */}
        <button
          type="button"
          onClick={toggleMode}
          title={t('mode.toggle_tooltip')}
          className={`flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium border transition-all ${
            mode === 'expert'
              ? 'bg-purple-50 border-purple-300 text-purple-700 shadow-xs'
              : 'bg-slate-100 hover:bg-slate-200 border-slate-200 text-slate-700'
          }`}
        >
          <Sliders className="w-3.5 h-3.5 text-blue-600" />
          <span>{mode === 'expert' ? t('mode.expert') : t('mode.simple')}</span>
        </button>

        {/* Language Toggle (EN / हिन्दी) */}
        <button
          type="button"
          onClick={toggleLanguage}
          title="Toggle Language (English / हिन्दी)"
          className="flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium bg-slate-100 hover:bg-slate-200 border border-slate-200 text-slate-700 transition-all"
        >
          <Languages className="w-3.5 h-3.5 text-indigo-600" />
          <span className="font-semibold">{language === 'en' ? 'EN' : 'HI (हिन्दी)'}</span>
        </button>

        {/* Contextual Help Button */}
        <button
          type="button"
          onClick={() => openHelp(getActiveHelpTopic(location.pathname))}
          title="Open Field Guide & Contextual Help"
          className="p-1.5 rounded-full bg-blue-50 hover:bg-blue-100 text-blue-700 border border-blue-200 transition-colors"
        >
          <HelpCircle className="w-4 h-4" />
        </button>

        {/* System Health Pill */}
        <div className="hidden lg:flex items-center gap-2 px-3 py-1 rounded-full bg-emerald-50 border border-emerald-200 text-emerald-700 text-xs font-mono font-medium">
          <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse" />
          <span>ENGINES READY</span>
        </div>

        {/* Security Officer Badge Pill */}
        <div className="flex items-center gap-2.5 pl-3 border-l border-slate-200">
          <div className="w-8 h-8 rounded-full bg-blue-100 border border-blue-300 flex items-center justify-center text-blue-700 text-xs font-bold font-mono">
            {user?.full_name?.charAt(0) || 'U'}
          </div>
          <div className="text-left hidden sm:block">
            <span className="block text-xs font-semibold text-slate-800 leading-tight">
              {user?.full_name}
            </span>
            <span className="block text-[10px] text-slate-500 font-mono">
              Badge: {user?.badge_number || 'STATION-01'}
            </span>
          </div>
        </div>
      </div>
    </header>
  );
};
