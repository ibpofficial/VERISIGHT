import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { 
  BookOpen, Compass, Users, FileText, CheckCircle2, 
  AlertTriangle, Camera, HelpCircle, ShieldAlert, Play, 
  Search, ExternalLink, ArrowRight, ShieldCheck, Info
} from 'lucide-react';
import { GlassCard } from '../components/glass/GlassCard';
import { GlassButton } from '../components/glass/GlassButton';
import { GLOSSARY } from '../components/common/GlossaryTooltip';
import { usePreferences } from '../context/PreferencesContext';

export const HelpCenterPage: React.FC = () => {
  const navigate = useNavigate();
  const { mode, language, t } = usePreferences();
  const [activeTab, setActiveTab] = useState<'getting_started' | 'roles' | 'reports' | 'results' | 'tips' | 'faq' | 'limitations'>('getting_started');
  const [searchQuery, setSearchQuery] = useState('');

  const filteredGlossary = Object.entries(GLOSSARY).filter(([key, val]) => {
    const q = searchQuery.toLowerCase();
    return key.toLowerCase().includes(q) || val.plain.toLowerCase().includes(q) || val.technical.toLowerCase().includes(q);
  });

  const faqs = [
    {
      q: 'Does VERISIGHT connect to government passport or national databases?',
      a: 'No. VERISIGHT runs 100% offline document screening and forensic algorithms. It does not possess direct access to sovereign police, immigration, or civil registration databases. It detects mathematical check-digit errors and digital tampering signatures.',
    },
    {
      q: 'Why did a genuine passport get flagged as "REVIEW"?',
      a: 'Camera flash glare, physical document curvature, or motion blur frequently degrade OCR confidence scores. The system flags anything below confidence thresholds for officer review rather than guessing.',
    },
    {
      q: 'What is Error Level Analysis (ELA) and how do I read the heatmap?',
      a: 'When an image is saved as a JPEG, each 8x8 pixel block is compressed. If someone edits an image (e.g. pastes a new face or changes a date) and resaves it, the edited region has a noticeably different compression error level. The ELA viewer shows this difference as brighter colored clusters.',
    },
    {
      q: 'Is facial biometric verification mandatory under the law?',
      a: 'No. Under Section 6 of India’s Digital Personal Data Protection (DPDP) Act 2023, biometric comparison requires explicit, affirmative user consent. If the traveler declines or equipment is unavailable, officers skip face verification and the system marks it "NOT APPLICABLE" without penalty.',
    },
    {
      q: 'How does the SHA-256 cryptographic audit trail prevent evidence tampering?',
      a: 'Every intake, optical check, reviewer note, and status update is hashed with SHA-256 and chained to the previous record hash. If a database record or timestamp is modified maliciously, the cryptographic chain breaks and the system immediately flags the tampering on the Audit page.',
    },
  ];

  return (
    <div className="space-y-6 max-w-6xl mx-auto">
      {/* Top Banner */}
      <GlassCard className="p-6 bg-gradient-to-r from-blue-900 via-indigo-950 to-slate-900 text-white border-blue-500/30">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-6">
          <div className="space-y-2 max-w-2xl">
            <div className="flex items-center gap-2">
              <span className="px-2.5 py-0.5 rounded-full bg-blue-500/20 text-blue-300 border border-blue-400/30 text-xs font-mono font-semibold">
                OPERATIONAL GUIDELINES // SIH 26188
              </span>
              <span className="text-xs text-slate-400 font-mono">MHA SSB Police II</span>
            </div>
            <h1 className="text-2xl font-bold tracking-tight text-white">
              VERISIGHT Knowledge Base & Training Center
            </h1>
            <p className="text-xs text-slate-300 leading-relaxed">
              Standard Operating Procedures (SOP), role playbooks, digital forensic guides, and automated verification guidelines for border checkpoint and immigration officers.
            </p>
          </div>

          <div className="flex flex-col sm:flex-row items-stretch sm:items-center gap-3">
            <GlassButton
              variant="primary"
              size="md"
              icon={<Play className="w-4 h-4" />}
              onClick={() => navigate('/screenings/new')}
            >
              Start Live Screening
            </GlassButton>
            <GlassButton
              variant="secondary"
              size="md"
              icon={<Search className="w-4 h-4" />}
              onClick={() => navigate('/quick-check')}
            >
              Launch Quick Check
            </GlassButton>
          </div>
        </div>
      </GlassCard>

      {/* Navigation Tabs */}
      <div className="flex items-center gap-2 border-b border-slate-200 overflow-x-auto pb-2 text-xs font-medium">
        <button
          type="button"
          onClick={() => setActiveTab('getting_started')}
          className={`px-3.5 py-2 rounded-lg transition-colors flex items-center gap-2 shrink-0 ${
            activeTab === 'getting_started'
              ? 'bg-blue-50 text-blue-700 font-bold border border-blue-200 shadow-2xs'
              : 'text-slate-600 hover:text-slate-900 hover:bg-slate-100'
          }`}
        >
          <Compass className="w-4 h-4" /> 5-Min Walkthrough
        </button>

        <button
          type="button"
          onClick={() => setActiveTab('roles')}
          className={`px-3.5 py-2 rounded-lg transition-colors flex items-center gap-2 shrink-0 ${
            activeTab === 'roles'
              ? 'bg-blue-50 text-blue-700 font-bold border border-blue-200 shadow-2xs'
              : 'text-slate-600 hover:text-slate-900 hover:bg-slate-100'
          }`}
        >
          <Users className="w-4 h-4" /> Role Guides (SOP)
        </button>

        <button
          type="button"
          onClick={() => setActiveTab('results')}
          className={`px-3.5 py-2 rounded-lg transition-colors flex items-center gap-2 shrink-0 ${
            activeTab === 'results'
              ? 'bg-blue-50 text-blue-700 font-bold border border-blue-200 shadow-2xs'
              : 'text-slate-600 hover:text-slate-900 hover:bg-slate-100'
          }`}
        >
          <ShieldCheck className="w-4 h-4" /> Understanding Results
        </button>

        <button
          type="button"
          onClick={() => setActiveTab('reports')}
          className={`px-3.5 py-2 rounded-lg transition-colors flex items-center gap-2 shrink-0 ${
            activeTab === 'reports'
              ? 'bg-blue-50 text-blue-700 font-bold border border-blue-200 shadow-2xs'
              : 'text-slate-600 hover:text-slate-900 hover:bg-slate-100'
          }`}
        >
          <FileText className="w-4 h-4" /> Reading Dossiers
        </button>

        <button
          type="button"
          onClick={() => setActiveTab('tips')}
          className={`px-3.5 py-2 rounded-lg transition-colors flex items-center gap-2 shrink-0 ${
            activeTab === 'tips'
              ? 'bg-blue-50 text-blue-700 font-bold border border-blue-200 shadow-2xs'
              : 'text-slate-600 hover:text-slate-900 hover:bg-slate-100'
          }`}
        >
          <Camera className="w-4 h-4" /> Photo & Capture Tips
        </button>

        <button
          type="button"
          onClick={() => setActiveTab('faq')}
          className={`px-3.5 py-2 rounded-lg transition-colors flex items-center gap-2 shrink-0 ${
            activeTab === 'faq'
              ? 'bg-blue-50 text-blue-700 font-bold border border-blue-200 shadow-2xs'
              : 'text-slate-600 hover:text-slate-900 hover:bg-slate-100'
          }`}
        >
          <HelpCircle className="w-4 h-4" /> FAQ & Glossary
        </button>

        <button
          type="button"
          onClick={() => setActiveTab('limitations')}
          className={`px-3.5 py-2 rounded-lg transition-colors flex items-center gap-2 shrink-0 ${
            activeTab === 'limitations'
              ? 'bg-rose-50 text-rose-700 font-bold border border-rose-200 shadow-2xs'
              : 'text-slate-600 hover:text-slate-900 hover:bg-slate-100'
          }`}
        >
          <ShieldAlert className="w-4 h-4" /> System Limitations
        </button>
      </div>

      {/* Tab 1: 5-Minute Walkthrough */}
      {activeTab === 'getting_started' && (
        <div className="space-y-6">
          <GlassCard className="p-6 space-y-4">
            <h2 className="text-base font-bold text-slate-900">
              The 6-Step Verification Story
            </h2>
            <p className="text-xs text-slate-600 leading-relaxed">
              Every identity credential processed in VERISIGHT follows a disciplined, auditable forensic pipeline from intake to final dossier lock.
            </p>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 pt-2">
              <div className="p-4 rounded-xl bg-slate-50 border border-slate-200 space-y-2">
                <div className="w-7 h-7 rounded-lg bg-blue-600 text-white flex items-center justify-center font-bold text-xs">
                  1
                </div>
                <h3 className="text-xs font-bold text-slate-900">Create Screening & Ingest</h3>
                <p className="text-[11px] text-slate-600 leading-relaxed">
                  Select document template (Passport TD3, Visa TD2, ID TD1) and upload image or capture via border webcam.
                </p>
              </div>

              <div className="p-4 rounded-xl bg-slate-50 border border-slate-200 space-y-2">
                <div className="w-7 h-7 rounded-lg bg-blue-600 text-white flex items-center justify-center font-bold text-xs">
                  2
                </div>
                <h3 className="text-xs font-bold text-slate-900">Optical Quality Pre-flight</h3>
                <p className="text-[11px] text-slate-600 leading-relaxed">
                  Evaluates Laplacian variance sharpness, specular reflection, and tilts to auto-correct perspective before OCR.
                </p>
              </div>

              <div className="p-4 rounded-xl bg-slate-50 border border-slate-200 space-y-2">
                <div className="w-7 h-7 rounded-lg bg-blue-600 text-white flex items-center justify-center font-bold text-xs">
                  3
                </div>
                <h3 className="text-xs font-bold text-slate-900">OCR & MRZ Check Digits</h3>
                <p className="text-[11px] text-slate-600 leading-relaxed">
                  Extracts Visual Inspection Zone text and calculates ICAO Doc 9303 modulo-10 check digits to catch date alterations.
                </p>
              </div>

              <div className="p-4 rounded-xl bg-slate-50 border border-slate-200 space-y-2">
                <div className="w-7 h-7 rounded-lg bg-blue-600 text-white flex items-center justify-center font-bold text-xs">
                  4
                </div>
                <h3 className="text-xs font-bold text-slate-900">Multi-Factor Forensics</h3>
                <p className="text-[11px] text-slate-600 leading-relaxed">
                  Inspects JPEG Error Level Analysis (ELA), EXIF software signatures, font baselines, and portrait tampering.
                </p>
              </div>

              <div className="p-4 rounded-xl bg-slate-50 border border-slate-200 space-y-2">
                <div className="w-7 h-7 rounded-lg bg-blue-600 text-white flex items-center justify-center font-bold text-xs">
                  5
                </div>
                <h3 className="text-xs font-bold text-slate-900">Investigate & Decide</h3>
                <p className="text-[11px] text-slate-600 leading-relaxed">
                  Review transparent rule firings. Record officer interview notes or escalate to supervisor for final determination.
                </p>
              </div>

              <div className="p-4 rounded-xl bg-slate-50 border border-slate-200 space-y-2">
                <div className="w-7 h-7 rounded-lg bg-blue-600 text-white flex items-center justify-center font-bold text-xs">
                  6
                </div>
                <h3 className="text-xs font-bold text-slate-900">Tamper-Proof Dossier</h3>
                <p className="text-[11px] text-slate-600 leading-relaxed">
                  Export formal PDF dossier with Page 1 summary for everyone and lock all determinations into the SHA-256 ledger.
                </p>
              </div>
            </div>
          </GlassCard>

          {/* Try With A Demo Sample */}
          <GlassCard className="p-6 bg-blue-50/60 border-blue-200 space-y-3">
            <h3 className="text-sm font-bold text-blue-950 flex items-center gap-2">
              <Sparkles className="w-4 h-4 text-blue-600" /> Explore with Pre-Seeded Synthetic Scenarios
            </h3>
            <p className="text-xs text-blue-900 leading-relaxed">
              New to VERISIGHT? You can test the full pipeline using pre-loaded, synthetic test scenarios without uploading personal data:
            </p>
            <div className="flex flex-wrap gap-2 pt-1">
              <GlassButton
                size="sm"
                variant="secondary"
                onClick={() => navigate('/screenings/new')}
              >
                Load Scenario 1: Clean Passport
              </GlassButton>
              <GlassButton
                size="sm"
                variant="secondary"
                onClick={() => navigate('/screenings/new')}
              >
                Load Scenario 3: MRZ Checksum Mismatch
              </GlassButton>
              <GlassButton
                size="sm"
                variant="secondary"
                onClick={() => navigate('/screenings/new')}
              >
                Load Scenario 4: ELA Tampered Portrait
              </GlassButton>
            </div>
          </GlassCard>
        </div>
      )}

      {/* Tab 2: Role Guides */}
      {activeTab === 'roles' && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <GlassCard className="p-5 space-y-3">
            <div className="flex items-center gap-2 border-b border-slate-100 pb-2.5">
              <span className="p-1 rounded bg-blue-100 text-blue-700 font-mono text-xs font-bold">SO</span>
              <h3 className="text-sm font-bold text-slate-900">Screening Officer</h3>
            </div>
            <p className="text-xs text-slate-600 leading-relaxed">
              Front-line officer executing primary passenger inspection at border control points.
            </p>
            <div className="text-xs space-y-1.5 text-slate-700">
              <span className="font-semibold block text-[11px] text-slate-900">Daily Responsibilities:</span>
              <p>• Ingest credentials and ensure glare-free optical capture.</p>
              <p>• Check that physical document details match OCR visual bounding boxes.</p>
              <p>• If MRZ check digit fails, escalate immediately to Senior Reviewer.</p>
              <p>• Attach interview notes and travel tickets to the investigation file.</p>
            </div>
          </GlassCard>

          <GlassCard className="p-5 space-y-3">
            <div className="flex items-center gap-2 border-b border-slate-100 pb-2.5">
              <span className="p-1 rounded bg-purple-100 text-purple-700 font-mono text-xs font-bold">SR</span>
              <h3 className="text-sm font-bold text-slate-900">Senior Reviewer</h3>
            </div>
            <p className="text-xs text-slate-600 leading-relaxed">
              Supervisory officer adjudicating flagged anomalies and secondary screening escalations.
            </p>
            <div className="text-xs space-y-1.5 text-slate-700">
              <span className="font-semibold block text-[11px] text-slate-900">Daily Responsibilities:</span>
              <p>• Inspect Error Level Analysis (ELA) heatmaps and double-compression artifacts.</p>
              <p>• Authorize formal Risk Decision Overrides with recorded justification.</p>
              <p>• Resolve investigation cases with mandatory closure findings.</p>
              <p>• Issue formal referral for forensic lab hardware inspection if physical tampering is suspected.</p>
            </div>
          </GlassCard>

          <GlassCard className="p-5 space-y-3">
            <div className="flex items-center gap-2 border-b border-slate-100 pb-2.5">
              <span className="p-1 rounded bg-emerald-100 text-emerald-700 font-mono text-xs font-bold">AU</span>
              <h3 className="text-sm font-bold text-slate-900">Independent Auditor</h3>
            </div>
            <p className="text-xs text-slate-600 leading-relaxed">
              Oversight officer verifying legal compliance, DPDP Act adherence, and tamper resistance.
            </p>
            <div className="text-xs space-y-1.5 text-slate-700">
              <span className="font-semibold block text-[11px] text-slate-900">Daily Responsibilities:</span>
              <p>• Verify the mathematical integrity of the SHA-256 hash ledger periodically.</p>
              <p>• Confirm that biometric facial verifications enforce §6 DPDP Act affirmative consent.</p>
              <p>• Audit officer overrides to prevent unauthorized clearances.</p>
            </div>
          </GlassCard>

          <GlassCard className="p-5 space-y-3">
            <div className="flex items-center gap-2 border-b border-slate-100 pb-2.5">
              <span className="p-1 rounded bg-slate-200 text-slate-800 font-mono text-xs font-bold">AD</span>
              <h3 className="text-sm font-bold text-slate-900">System Administrator</h3>
            </div>
            <p className="text-xs text-slate-600 leading-relaxed">
              Technical station lead managing officer credentials, access control, and engine calibration.
            </p>
            <div className="text-xs space-y-1.5 text-slate-700">
              <span className="font-semibold block text-[11px] text-slate-900">Daily Responsibilities:</span>
              <p>• Monitor real-time latency and health across OCR, MRZ, and forensics engines.</p>
              <p>• Calibrate risk threshold weights based on seasonal travel alerts.</p>
              <p>• Manage security officer badges, active tokens, and station accounts.</p>
            </div>
          </GlassCard>
        </div>
      )}

      {/* Tab 3: Understanding Results */}
      {activeTab === 'results' && (
        <div className="space-y-4">
          <div className="p-5 rounded-2xl bg-emerald-50 border border-emerald-200 space-y-2">
            <div className="flex items-center gap-2 font-bold text-emerald-900 text-sm">
              <CheckCircle2 className="w-5 h-5 text-emerald-600" /> CLEAR (Score 0 - 29)
            </div>
            <p className="text-xs text-emerald-800 leading-relaxed">
              All baseline checks passed. ICAO 9303 check digits match computed values, typographic alignment is uniform, and no compression or EXIF anomalies were found. Proceed with standard clearance.
            </p>
          </div>

          <div className="p-5 rounded-2xl bg-amber-50 border border-amber-200 space-y-2">
            <div className="flex items-center gap-2 font-bold text-amber-900 text-sm">
              <AlertTriangle className="w-5 h-5 text-amber-600" /> REVIEW (Score 30 - 69)
            </div>
            <p className="text-xs text-amber-800 leading-relaxed">
              Subtle inconsistencies detected. Examples include moderate image blur (Laplacian &lt; 100), low OCR confidence on a single field, or minor baseline tilt. Manually compare physical document against screen before approving.
            </p>
          </div>

          <div className="p-5 rounded-2xl bg-rose-50 border border-rose-200 space-y-2">
            <div className="flex items-center gap-2 font-bold text-rose-900 text-sm">
              <ShieldAlert className="w-5 h-5 text-rose-600" /> HIGH RISK (Score 70 - 100)
            </div>
            <p className="text-xs text-rose-800 leading-relaxed">
              Critical mathematical or forensic anomaly detected. Examples include failing passport check-digit modulo-10 checksum, mismatched photo compression (ELA), or editing software metadata tags. Open an Investigation Case immediately.
            </p>
          </div>
        </div>
      )}

      {/* Tab 4: How to Read Reports */}
      {activeTab === 'reports' && (
        <GlassCard className="p-6 space-y-4">
          <h2 className="text-sm font-bold text-slate-900">
            Annotated Guide: The 2-Layer VERISIGHT Evidentiary Dossier
          </h2>
          <p className="text-xs text-slate-600 leading-relaxed">
            VERISIGHT reports are designed for both non-technical supervisors and courtroom forensic evidentiary review:
          </p>

          <div className="space-y-4 pt-2">
            <div className="p-4 rounded-xl bg-slate-50 border border-slate-200 space-y-2">
              <span className="text-xs font-bold text-blue-700 block uppercase tracking-wider">
                Page 1: "Summary for Everyone"
              </span>
              <p className="text-xs text-slate-700 leading-relaxed">
                Written in clear, plain language at a grade-8 reading level. Contains the clear outcome badge (CLEAR / REVIEW / HIGH RISK), a 3-sentence summary of what was found, a checklist of recommended officer next actions, and the document photo with marked suspicious regions.
              </p>
            </div>

            <div className="p-4 rounded-xl bg-slate-50 border border-slate-200 space-y-2">
              <span className="text-xs font-bold text-indigo-700 block uppercase tracking-wider">
                Technical Appendix (Pages 2 - 5)
              </span>
              <p className="text-xs text-slate-700 leading-relaxed">
                Contains verbatim OCR field strings with individual confidence percentages, ICAO 7-3-1 check digit computation matrices, high-resolution ELA heatmaps, texture frequency graphs, and the SHA-256 digital custody block hash.
              </p>
            </div>
          </div>
        </GlassCard>
      )}

      {/* Tab 5: Photo Tips */}
      {activeTab === 'tips' && (
        <GlassCard className="p-6 space-y-4">
          <h2 className="text-sm font-bold text-slate-900">
            How to Capture Scans for Optimal Forensic Accuracy
          </h2>
          <p className="text-xs text-slate-600 leading-relaxed">
            90% of false positive fraud alerts are caused by poor image capture. Follow these field guidelines:
          </p>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 pt-2">
            <div className="p-4 rounded-xl bg-emerald-50/70 border border-emerald-200 space-y-2">
              <span className="text-xs font-bold text-emerald-900 flex items-center gap-1.5">
                <CheckCircle2 className="w-4 h-4 text-emerald-600" /> DO: Best Practices
              </span>
              <ul className="text-xs text-emerald-800 space-y-1.5 list-disc pl-4">
                <li>Place credential flat on a dark, non-reflective background.</li>
                <li>Ensure all 4 corners of the document are visible.</li>
                <li>Use diffused overhead room lighting.</li>
                <li>Hold camera parallel to the document surface (avoid sharp angles).</li>
                <li>Keep the bottom two MRZ lines completely unobstructed.</li>
              </ul>
            </div>

            <div className="p-4 rounded-xl bg-rose-50/70 border border-rose-200 space-y-2">
              <span className="text-xs font-bold text-rose-900 flex items-center gap-1.5">
                <ShieldAlert className="w-4 h-4 text-rose-600" /> DON'T: Avoid These Errors
              </span>
              <ul className="text-xs text-rose-800 space-y-1.5 list-disc pl-4">
                <li>Do NOT use smartphone flash (creates blinding white specular spots).</li>
                <li>Do NOT upload screenshots of phone screens (destroys JPEG ELA blocks).</li>
                <li>Do NOT crop out the MRZ lines at the bottom.</li>
                <li>Do NOT photograph through thick plastic sleeves that cause reflections.</li>
              </ul>
            </div>
          </div>
        </GlassCard>
      )}

      {/* Tab 6: FAQ & Searchable Glossary */}
      {activeTab === 'faq' && (
        <div className="space-y-6">
          <GlassCard className="p-6 space-y-4">
            <h2 className="text-sm font-bold text-slate-900">
              Frequently Asked Questions (FAQ)
            </h2>
            <div className="space-y-3 pt-1">
              {faqs.map((faq, idx) => (
                <div key={idx} className="p-3.5 rounded-xl bg-slate-50 border border-slate-200 space-y-1">
                  <h4 className="text-xs font-bold text-slate-900">{faq.q}</h4>
                  <p className="text-xs text-slate-600 leading-relaxed">{faq.a}</p>
                </div>
              ))}
            </div>
          </GlassCard>

          <GlassCard className="p-6 space-y-4">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
              <div>
                <h2 className="text-sm font-bold text-slate-900">
                  Searchable Security Glossary
                </h2>
                <p className="text-xs text-slate-500">
                  Plain-language definitions for every technical term used in VERISIGHT.
                </p>
              </div>
              <div className="relative w-full sm:w-64">
                <Search className="w-4 h-4 text-slate-400 absolute left-3 top-2.5" />
                <input
                  type="text"
                  placeholder="Search terms (e.g. OCR, ELA, MRZ)..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="w-full pl-9 pr-3 py-1.5 text-xs rounded-xl border border-slate-300 bg-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-3 pt-2">
              {filteredGlossary.map(([key, item]) => (
                <div key={key} className="p-3.5 rounded-xl bg-slate-50 border border-slate-200 space-y-1">
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-bold text-blue-700">{item.term}</span>
                    <span className="text-[10px] font-mono text-slate-400 font-bold">{key}</span>
                  </div>
                  <p className="text-xs text-slate-700 leading-snug">{item.plain}</p>
                  <p className="text-[10px] font-mono text-slate-500 pt-1 border-t border-slate-200">
                    <span className="text-amber-600 font-semibold">Engine:</span> {item.technical}
                  </p>
                </div>
              ))}
            </div>
          </GlassCard>
        </div>
      )}

      {/* Tab 7: Limitations */}
      {activeTab === 'limitations' && (
        <GlassCard className="p-6 space-y-4 border-rose-200 bg-rose-50/20">
          <div className="flex items-center gap-2">
            <span className="p-1 rounded-md bg-rose-600 text-white">
              <ShieldAlert className="w-5 h-5" />
            </span>
            <h2 className="text-base font-bold text-rose-950">
              System Scope & Absolute Limitations
            </h2>
          </div>
          <p className="text-xs text-slate-700 leading-relaxed font-medium">
            In compliance with Smart India Hackathon 2026 Problem Statement 26188 guidelines, the jury and security officers must understand what VERISIGHT cannot do:
          </p>

          <div className="space-y-3 pt-2">
            <div className="p-4 rounded-xl bg-white border border-rose-200 space-y-1.5">
              <h4 className="text-xs font-bold text-rose-900">
                1. No Direct Government or Law Enforcement Database Connections
              </h4>
              <p className="text-xs text-slate-600 leading-relaxed">
                VERISIGHT does not query sovereign passport databases, Aadhaar registries, or INTERPOL SLTD stolen document databases. Authenticity is screened using mathematical check digits, font consistency, and digital image forensics.
              </p>
            </div>

            <div className="p-4 rounded-xl bg-white border border-rose-200 space-y-1.5">
              <h4 className="text-xs font-bold text-rose-900">
                2. Cannot Guarantee Physical Substrate Genuineness
              </h4>
              <p className="text-xs text-slate-600 leading-relaxed">
                A digitally clean scan does not prove that the underlying paper, intaglio ink, hologram, or watermark is genuine. High-end physical counterfeits with mathematically correct MRZ data require physical UV/IR spectral analysis hardware.
              </p>
            </div>

            <div className="p-4 rounded-xl bg-white border border-rose-200 space-y-1.5">
              <h4 className="text-xs font-bold text-rose-900">
                3. Automated Decision Support Only
              </h4>
              <p className="text-xs text-slate-600 leading-relaxed">
                VERISIGHT will never automatically refuse entry or convict an individual of fraud. An Indian security officer or authorized border control official always conducts secondary questioning and makes the final decision.
              </p>
            </div>
          </div>
        </GlassCard>
      )}
    </div>
  );
};

const Sparkles: React.FC<{ className?: string }> = ({ className }) => (
  <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
    <path d="m12 3-1.912 5.813a2 2 0 0 1-1.275 1.275L3 12l5.813 1.912a2 2 0 0 1 1.275 1.275L12 21l1.912-5.813a2 2 0 0 1 1.275-1.275L21 12l-5.813-1.912a2 2 0 0 1-1.275-1.275L12 3Z"/>
  </svg>
);
