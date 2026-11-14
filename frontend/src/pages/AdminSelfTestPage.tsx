import React, { useState, useEffect } from 'react';
import { 
  Activity, CheckCircle2, XCircle, RefreshCw, 
  Cpu, Database, ShieldCheck, FileText, Layers, Zap
} from 'lucide-react';
import { GlassCard } from '../components/glass/GlassCard';
import { GlassButton } from '../components/glass/GlassButton';
import { apiClient } from '../services/api';

export const AdminSelfTestPage: React.FC = () => {
  const [data, setData] = useState<any | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const runDiagnostics = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const res = await apiClient.get('/admin/self-test');
      setData(res.data);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to execute system diagnostics.');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    runDiagnostics();
  }, []);

  const componentIcons: Record<string, React.ReactNode> = {
    opencv: <Cpu className="w-5 h-5 text-blue-600" />,
    pillow: <Layers className="w-5 h-5 text-indigo-600" />,
    reportlab: <FileText className="w-5 h-5 text-purple-600" />,
    database: <Database className="w-5 h-5 text-emerald-600" />,
    audit_chain: <ShieldCheck className="w-5 h-5 text-emerald-600" />,
    quick_check: <Zap className="w-5 h-5 text-amber-500" />,
    mrz_engine: <Activity className="w-5 h-5 text-sky-600" />,
  };

  return (
    <div className="space-y-6 max-w-6xl mx-auto select-none">
      {/* Header */}
      <GlassCard className="p-6 bg-gradient-to-r from-blue-900 via-slate-900 to-indigo-950 text-white border-blue-400/20">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div className="space-y-1">
            <div className="flex items-center gap-2">
              <span className="p-1 rounded bg-blue-500/20 text-blue-300 font-mono text-xs font-bold">
                DIAGNOSTICS & BENCHMARK
              </span>
              <span className="text-xs text-slate-400 font-mono">SIH 26188 Hardening</span>
            </div>
            <h1 className="text-2xl font-bold tracking-tight text-white">
              System Self-Test & Subsystem Health
            </h1>
            <p className="text-xs text-slate-300 max-w-2xl leading-relaxed">
              Executes live operational integration probes across OpenCV, Pillow, ReportLab, SQLite, SHA-256 Merkle Ledger, and ICAO 9303 Check Digit algorithms.
            </p>
          </div>

          <div className="flex items-center gap-3">
            <GlassButton
              variant="primary"
              size="md"
              onClick={runDiagnostics}
              disabled={isLoading}
              icon={isLoading ? <RefreshCw className="w-4 h-4 animate-spin" /> : <RefreshCw className="w-4 h-4" />}
            >
              {isLoading ? 'Running Probes...' : 'Rerun Self-Test'}
            </GlassButton>
          </div>
        </div>
      </GlassCard>

      {/* Overall Health Status Banner */}
      {data && (
        <div className={`p-5 rounded-2xl border flex items-center justify-between gap-4 shadow-xs ${
          data.status === 'SYSTEM_OPERATIONAL'
            ? 'bg-emerald-50 text-emerald-900 border-emerald-300'
            : 'bg-rose-50 text-rose-900 border-rose-300'
        }`}>
          <div className="flex items-center gap-3">
            <div className={`w-9 h-9 rounded-xl flex items-center justify-center text-white ${
              data.status === 'SYSTEM_OPERATIONAL' ? 'bg-emerald-600' : 'bg-rose-600'
            }`}>
              {data.status === 'SYSTEM_OPERATIONAL' ? <CheckCircle2 className="w-5 h-5" /> : <XCircle className="w-5 h-5" />}
            </div>
            <div>
              <span className="text-[10px] uppercase font-mono font-bold tracking-wider opacity-75">
                Core Diagnostic Determination
              </span>
              <h2 className="text-base font-bold">
                {data.status === 'SYSTEM_OPERATIONAL' ? 'ALL SYSTEM SUBSYSTEMS FULLY OPERATIONAL' : 'SYSTEM DEGRADED — INSPECT COMPONENT LOGS'}
              </h2>
            </div>
          </div>

          <div className="text-right font-mono text-xs hidden sm:block">
            <span className="block text-[11px] opacity-80">Total Probe Latency</span>
            <span className="font-bold text-sm">{data.total_latency_ms} ms</span>
          </div>
        </div>
      )}

      {error && (
        <div className="p-4 rounded-xl bg-red-50 border border-red-200 text-red-800 text-xs">
          {error}
        </div>
      )}

      {/* Component Grid */}
      {data?.components && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {Object.entries(data.components).map(([key, comp]: [string, any]) => (
            <GlassCard key={key} className="p-5 space-y-3">
              <div className="flex items-center justify-between border-b border-slate-100 pb-2.5">
                <div className="flex items-center gap-2.5">
                  <div className="p-1.5 rounded-lg bg-slate-100">
                    {componentIcons[key] || <Activity className="w-5 h-5 text-slate-600" />}
                  </div>
                  <div>
                    <h3 className="text-xs font-bold text-slate-900 leading-snug">
                      {comp.name}
                    </h3>
                    <span className="text-[10px] font-mono text-slate-400">
                      Version: {comp.version}
                    </span>
                  </div>
                </div>

                <div className="flex items-center gap-2">
                  <span className="text-[10px] font-mono font-bold text-slate-500 bg-slate-100 px-2 py-0.5 rounded">
                    {comp.latency_ms} ms
                  </span>
                  <span className={`text-[10px] font-mono font-bold px-2 py-0.5 rounded-full border ${
                    comp.status === 'HEALTHY'
                      ? 'bg-emerald-50 text-emerald-700 border-emerald-200'
                      : 'bg-rose-50 text-rose-700 border-rose-200'
                  }`}>
                    {comp.status}
                  </span>
                </div>
              </div>

              <p className="text-xs text-slate-600 leading-relaxed font-medium">
                {comp.detail || comp.error}
              </p>
            </GlassCard>
          ))}
        </div>
      )}
    </div>
  );
};
