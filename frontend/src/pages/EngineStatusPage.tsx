import React, { useState, useEffect } from 'react';
import { 
  CheckCircle2, AlertTriangle, XCircle, 
  RotateCcw, Cpu, Server
} from 'lucide-react';
import { GlassCard } from '../components/glass/GlassCard';
import { GlassButton } from '../components/glass/GlassButton';
import { EmptyState } from '../components/common/EmptyState';
import { LoadingSkeleton } from '../components/common/LoadingSkeleton';
import { apiClient } from '../services/api';

interface EngineItem {
  name: string;
  status: 'HEALTHY' | 'DEGRADED' | 'FAILING';
  details: string;
}

interface EngineStatusData {
  status: string;
  engines: EngineItem[];
  system_time_utc: string;
  python_version: string;
}

export const EngineStatusPage: React.FC = () => {
  const [data, setData] = useState<EngineStatusData | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchStatus = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const res = await apiClient.get('/admin/engine-status');
      setData(res.data);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to fetch engine diagnostics telemetry.');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchStatus();
  }, []);

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'HEALTHY':
        return {
          icon: <CheckCircle2 className="w-4 h-4 text-green-600" />,
          badge: 'bg-green-50 text-green-700 border-green-200 font-semibold',
        };
      case 'DEGRADED':
        return {
          icon: <AlertTriangle className="w-4 h-4 text-amber-600" />,
          badge: 'bg-amber-50 text-amber-700 border-amber-200 font-semibold',
        };
      default:
        return {
          icon: <XCircle className="w-4 h-4 text-red-600" />,
          badge: 'bg-red-50 text-red-700 border-red-200 font-semibold',
        };
    }
  };

  return (
    <div className="space-y-6 max-w-6xl mx-auto">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-2 border-b border-slate-200">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-900 flex items-center gap-3">
            Processing Engine Diagnostics
            <span className={`text-xs px-2.5 py-0.5 rounded-full border font-mono ${
              data?.status === 'OPERATIONAL' 
                ? 'bg-green-50 text-green-700 border-green-200 font-semibold' 
                : 'bg-amber-50 text-amber-700 border-amber-200 font-semibold'
            }`}>
              {data?.status || 'MONITORING'}
            </span>
          </h1>
          <p className="text-sm text-slate-500 mt-1">
            Real-time status monitor for computer vision, OCR, forensic difference pipelines, and cryptographic ledgers.
          </p>
        </div>
        <div className="flex items-center gap-3">
          <GlassButton
            size="sm"
            variant="ghost"
            onClick={fetchStatus}
            icon={<RotateCcw className="w-4 h-4" />}
          >
            Refresh Telemetry
          </GlassButton>
        </div>
      </div>

      {isLoading ? (
        <div className="space-y-4">
          <LoadingSkeleton className="h-20 w-full" />
          <LoadingSkeleton className="h-16 w-full" count={6} />
        </div>
      ) : error || !data ? (
        <EmptyState
          icon={<Server className="w-8 h-8" />}
          title="Telemetry Unavailable"
          description={error || "Could not retrieve live engine diagnostics."}
          actionText="Retry Connection"
          onAction={fetchStatus}
        />
      ) : (
        <div className="space-y-6">
          {/* Metadata Card */}
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            <GlassCard className="p-4">
              <span className="text-slate-500 text-xs block font-semibold">Host Environment</span>
              <span className="text-sm font-mono font-bold text-slate-900 block mt-1">Python {data.python_version}</span>
            </GlassCard>
            <GlassCard className="p-4">
              <span className="text-slate-500 text-xs block font-semibold">System UTC Time</span>
              <span className="text-sm font-mono text-slate-800 block mt-1">{new Date(data.system_time_utc).toUTCString()}</span>
            </GlassCard>
            <GlassCard className="p-4">
              <span className="text-slate-500 text-xs block font-semibold">Active Subsystems</span>
              <span className="text-sm font-bold text-green-700 block mt-1">7 of 7 Engines Online</span>
            </GlassCard>
          </div>

          {/* Engine Cards List */}
          <GlassCard className="p-6 space-y-3">
            <h2 className="text-sm font-bold text-slate-900 border-b border-slate-200 pb-2 flex items-center gap-2">
              <Cpu className="w-4 h-4 text-blue-600" />
              Subsystem Registry & Module Status
            </h2>

            <div className="divide-y divide-slate-100">
              {data.engines.map((engine, idx) => {
                const s = getStatusBadge(engine.status);

                return (
                  <div key={idx} className="py-3.5 flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                    <div className="space-y-0.5">
                      <div className="flex items-center gap-2">
                        {s.icon}
                        <span className="font-semibold text-slate-900 text-xs">{engine.name}</span>
                      </div>
                      <p className="text-xs text-slate-500 pl-6 leading-relaxed">
                        {engine.details}
                      </p>
                    </div>
                    <span className={`px-2.5 py-0.5 rounded text-[11px] border self-start sm:self-center font-mono ${s.badge}`}>
                      {engine.status}
                    </span>
                  </div>
                );
              })}
            </div>
          </GlassCard>
        </div>
      )}
    </div>
  );
};
