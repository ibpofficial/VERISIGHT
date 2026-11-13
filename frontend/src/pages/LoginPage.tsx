import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { ShieldAlert, Lock, Mail, ArrowRight, ShieldCheck, UserCheck } from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { GlassCard } from '../components/glass/GlassCard';
import { GlassInput } from '../components/glass/GlassInput';
import { GlassButton } from '../components/glass/GlassButton';

export const LoginPage: React.FC = () => {
  const { login } = useAuth();
  const navigate = useNavigate();

  const [email, setEmail] = useState('officer@verisight.gov.in');
  const [password, setPassword] = useState('Officer@12345');
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setIsLoading(true);

    try {
      await login(email, password);
      navigate('/dashboard');
    } catch (err: any) {
      setError(
        err.response?.data?.detail || 'Authentication failed. Please verify credentials.'
      );
    } finally {
      setIsLoading(false);
    }
  };

  const setRoleCredentials = (roleEmail: string, rolePass: string) => {
    setEmail(roleEmail);
    setPassword(rolePass);
    setError(null);
  };

  return (
    <div className="min-h-screen bg-[#F1F5F9] flex flex-col justify-between p-4 sm:p-6 relative overflow-hidden w-full max-w-[100vw]">
      {/* Background Subtle Gradient Blobs */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        <div className="absolute top-1/4 left-1/3 w-96 h-96 bg-blue-100/70 rounded-full blur-3xl" />
        <div className="absolute bottom-1/3 right-1/4 w-80 h-80 bg-sky-100/80 rounded-full blur-3xl" />
      </div>

      {/* Header */}
      <header className="relative z-10 flex items-center justify-between max-w-5xl mx-auto w-full">
        <div className="flex items-center gap-3 min-w-0">
          <div className="w-10 h-10 shrink-0 rounded-xl bg-gradient-to-tr from-blue-600 to-sky-500 flex items-center justify-center shadow-md shadow-blue-500/20">
            <ShieldAlert className="w-6 h-6 text-white" />
          </div>
          <div className="min-w-0">
            <h1 className="text-base font-bold tracking-wider text-slate-900 truncate">VERISIGHT</h1>
            <p className="text-[10px] sm:text-[11px] text-slate-500 font-mono uppercase tracking-tight truncate">
              Ministry of Home Affairs • SSB Police II Division
            </p>
          </div>
        </div>
        <div className="hidden sm:flex items-center gap-2 text-xs font-mono text-slate-600 bg-white px-3 py-1.5 rounded-lg border border-slate-200/80 shadow-2xs shrink-0">
          <ShieldCheck className="w-4 h-4 text-emerald-600" />
          <span>SIH 2026 • PS 26188</span>
        </div>
      </header>

      {/* Main Login Card */}
      <div className="relative z-10 w-full max-w-sm sm:max-w-md mx-auto my-auto">
        <GlassCard className="p-6 sm:p-8 border border-slate-200/90 shadow-xl bg-white/95">
          <div className="text-center mb-6">
            <h2 className="text-xl font-bold text-slate-900 tracking-tight">
              Officer Portal Authentication
            </h2>
            <p className="text-xs text-slate-500 mt-1">
              Restricted workstation access for authorized border & immigration personnel.
            </p>
          </div>

          {error && (
            <div className="mb-5 p-3 rounded-lg bg-red-50 border border-red-200 text-red-700 text-xs font-mono font-medium">
              {error}
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-4">
            <GlassInput
              label="Official Email Identifier"
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="officer@verisight.gov.in"
              icon={<Mail className="w-4 h-4" />}
              required
            />

            <GlassInput
              label="Password / Security Passphrase"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="••••••••••••"
              icon={<Lock className="w-4 h-4" />}
              required
            />

            <div className="pt-2">
              <GlassButton
                type="submit"
                variant="primary"
                size="lg"
                isLoading={isLoading}
                className="w-full"
                icon={<ArrowRight className="w-4 h-4" />}
              >
                Authenticate & Access Console
              </GlassButton>
            </div>
          </form>

          {/* Demo Credentials Quick-Select Pill Grid */}
          <div className="mt-8 pt-6 border-t border-slate-100">
            <p className="text-[11px] font-mono uppercase text-slate-500 mb-2.5 flex items-center gap-1.5 font-semibold">
              <UserCheck className="w-3.5 h-3.5 text-blue-600" />
              <span>Demo Roles Quick Selector</span>
            </p>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 text-xs">
              <button
                type="button"
                onClick={() => setRoleCredentials('officer@verisight.gov.in', 'Officer@12345')}
                className="p-2.5 rounded-lg bg-slate-50 hover:bg-blue-50/70 border border-slate-200/80 hover:border-blue-300 text-left transition-colors cursor-pointer"
              >
                <div className="font-semibold text-slate-800">Screening Officer</div>
                <div className="text-[10px] text-slate-500 font-mono">Primary Triage</div>
              </button>
              <button
                type="button"
                onClick={() => setRoleCredentials('reviewer@verisight.gov.in', 'Reviewer@12345')}
                className="p-2.5 rounded-lg bg-slate-50 hover:bg-blue-50/70 border border-slate-200/80 hover:border-blue-300 text-left transition-colors cursor-pointer"
              >
                <div className="font-semibold text-slate-800">Senior Reviewer</div>
                <div className="text-[10px] text-slate-500 font-mono">Risk Overrides</div>
              </button>
              <button
                type="button"
                onClick={() => setRoleCredentials('admin@verisight.gov.in', 'Admin@12345')}
                className="p-2.5 rounded-lg bg-slate-50 hover:bg-blue-50/70 border border-slate-200/80 hover:border-blue-300 text-left transition-colors cursor-pointer"
              >
                <div className="font-semibold text-slate-800">Administrator</div>
                <div className="text-[10px] text-slate-500 font-mono">Full Privileges</div>
              </button>
              <button
                type="button"
                onClick={() => setRoleCredentials('auditor@verisight.gov.in', 'Auditor@12345')}
                className="p-2.5 rounded-lg bg-slate-50 hover:bg-blue-50/70 border border-slate-200/80 hover:border-blue-300 text-left transition-colors cursor-pointer"
              >
                <div className="font-semibold text-slate-800">Auditor</div>
                <div className="text-[10px] text-slate-500 font-mono">Chain Verification</div>
              </button>
            </div>
          </div>
        </GlassCard>
      </div>

      {/* Footer Notices */}
      <footer className="relative z-10 text-center text-[10px] sm:text-xs text-slate-500 font-mono w-full max-w-xl mx-auto px-4 py-2">
        <p className="break-words">
          NOTICE: All screening transactions and forensic audit blocks are cryptographically signed with SHA-256.
          Unauthorized access attempts are logged and reported.
        </p>
      </footer>
    </div>
  );
};
