import React, { useState, useEffect } from 'react';
import { 
  ShieldCheck, ShieldAlert, History, RotateCcw, 
  Search, Database, ChevronDown, ChevronRight
} from 'lucide-react';
import { GlassCard } from '../components/glass/GlassCard';
import { GlassButton } from '../components/glass/GlassButton';
import { EmptyState } from '../components/common/EmptyState';
import { LoadingSkeleton } from '../components/common/LoadingSkeleton';
import { auditApi } from '../services/api';
import type { AuditLogItem, AuditIntegrityResult } from '../types';

export const AuditPage: React.FC = () => {
  const [logs, setLogs] = useState<AuditLogItem[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Integrity verification state
  const [isVerifying, setIsVerifying] = useState(false);
  const [integrityResult, setIntegrityResult] = useState<AuditIntegrityResult | null>(null);

  // Expanded metadata rows
  const [expandedRowId, setExpandedRowId] = useState<number | null>(null);
  const [searchTerm, setSearchTerm] = useState('');

  const fetchLogs = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const data = await auditApi.list({ limit: 100 });
      setLogs(data);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to retrieve cryptographic audit logs.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleVerifyIntegrity = async () => {
    setIsVerifying(true);
    try {
      const res = await auditApi.verifyIntegrity();
      setIntegrityResult(res);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Cryptographic integrity verification check failed.');
    } finally {
      setIsVerifying(false);
    }
  };

  useEffect(() => {
    fetchLogs();
    handleVerifyIntegrity();
  }, []);

  const filteredLogs = logs.filter((log) => {
    if (!searchTerm) return true;
    const term = searchTerm.toLowerCase();
    return (
      log.event_type.toLowerCase().includes(term) ||
      log.action_description.toLowerCase().includes(term) ||
      log.current_hash.toLowerCase().includes(term) ||
      (log.screening_id && log.screening_id.toLowerCase().includes(term))
    );
  });

  return (
    <div className="space-y-6 max-w-7xl mx-auto">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-2 border-b border-slate-200">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-900 flex items-center gap-3">
            Cryptographic Audit Ledger
            <span className="text-xs px-2.5 py-0.5 rounded-full bg-blue-50 text-blue-700 border border-blue-200 font-semibold font-mono">
              SHA-256 Hash Chained
            </span>
          </h1>
          <p className="text-sm text-slate-500 mt-1">
            Tamper-evident, forward-secure audit ledger tracking all intake events, OCR corrections, and risk overrides.
          </p>
        </div>
        <div className="flex items-center gap-3">
          <GlassButton
            size="sm"
            variant="ghost"
            onClick={fetchLogs}
            icon={<RotateCcw className="w-4 h-4" />}
          >
            Refresh Logs
          </GlassButton>
          <GlassButton
            size="sm"
            variant="primary"
            onClick={handleVerifyIntegrity}
            disabled={isVerifying}
            icon={<ShieldCheck className="w-4 h-4" />}
          >
            {isVerifying ? 'Verifying Block Hashes...' : 'Verify Ledger Integrity'}
          </GlassButton>
        </div>
      </div>

      {error && (
        <div className="p-3 rounded-xl bg-red-50 border border-red-200 text-red-800 text-xs">
          {error}
        </div>
      )}

      {/* Integrity Seal Status Banner */}
      {integrityResult && (
        <div
          className={`p-5 rounded-2xl border flex flex-col md:flex-row md:items-center justify-between gap-4 transition shadow-sm ${
            integrityResult.is_intact
              ? 'bg-gradient-to-r from-green-50 to-emerald-50/50 border-green-200 text-green-950'
              : 'bg-red-50 border-red-300 text-red-950'
          }`}
        >
          <div className="flex items-start gap-4">
            {integrityResult.is_intact ? (
              <div className="w-12 h-12 rounded-xl bg-green-600 text-white flex items-center justify-center flex-shrink-0 shadow-md shadow-green-600/20">
                <ShieldCheck className="w-6 h-6" />
              </div>
            ) : (
              <div className="w-12 h-12 rounded-xl bg-red-600 text-white flex items-center justify-center flex-shrink-0 shadow-md shadow-red-600/20">
                <ShieldAlert className="w-6 h-6" />
              </div>
            )}
            <div>
              <div className="flex items-center gap-2">
                <h2 className="text-base font-bold">
                  {integrityResult.is_intact
                    ? 'Cryptographic Ledger Integrity Intact'
                    : 'Cryptographic Hash Linkage Compromised'}
                </h2>
                <span className="px-2 py-0.5 text-[10px] font-mono rounded bg-white/80 font-bold border">
                  {integrityResult.total_blocks_verified} BLOCKS VERIFIED
                </span>
              </div>
              <p className="text-xs text-slate-600 mt-1 leading-relaxed">
                {integrityResult.details}
              </p>
            </div>
          </div>

          {integrityResult.latest_hash && (
            <div className="text-right flex-shrink-0">
              <span className="text-[10px] font-mono text-slate-500 uppercase tracking-wider block">
                Latest Block Hash
              </span>
              <span className="font-mono text-xs text-slate-800 font-bold">
                {integrityResult.latest_hash.slice(0, 20)}...
              </span>
            </div>
          )}
        </div>
      )}

      {/* Filter & Search Bar */}
      <GlassCard className="p-4">
        <div className="relative">
          <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
          <input
            type="text"
            placeholder="Search by event type, action description, screening reference, or block hash..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full pl-9 pr-4 py-2 text-xs rounded-xl border border-slate-200 bg-white text-slate-800 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>
      </GlassCard>

      {/* Audit Log Table */}
      {isLoading ? (
        <div className="space-y-3">
          <LoadingSkeleton className="h-12 w-full" count={6} />
        </div>
      ) : filteredLogs.length === 0 ? (
        <EmptyState
          icon={<History className="w-8 h-8" />}
          title="No Audit Blocks Found"
          description="No ledger records matched the specified filter criteria."
          actionText="Clear Search"
          onAction={() => setSearchTerm('')}
        />
      ) : (
        <GlassCard className="p-0 overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-xs text-left">
              <thead>
                <tr className="border-b border-slate-200 text-slate-500 font-semibold bg-slate-50/70">
                  <th className="py-3 px-3 w-10"></th>
                  <th className="py-3 px-3">Block ID</th>
                  <th className="py-3 px-4">Event Type</th>
                  <th className="py-3 px-4">Actor & Role</th>
                  <th className="py-3 px-4">Action Summary</th>
                  <th className="py-3 px-4">Cryptographic Hash Digest</th>
                  <th className="py-3 px-4">Timestamp</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {filteredLogs.map((log) => {
                  const isExpanded = expandedRowId === log.id;

                  return (
                    <React.Fragment key={log.id}>
                      <tr
                        onClick={() => setExpandedRowId(isExpanded ? null : log.id)}
                        className="hover:bg-slate-50/60 cursor-pointer transition"
                      >
                        <td className="py-3 px-3 text-slate-400">
                          {isExpanded ? (
                            <ChevronDown className="w-3.5 h-3.5" />
                          ) : (
                            <ChevronRight className="w-3.5 h-3.5" />
                          )}
                        </td>
                        <td className="py-3 px-3 font-mono font-bold text-slate-700">
                          #{log.id}
                        </td>
                        <td className="py-3 px-4">
                          <span className="font-mono text-[11px] font-semibold text-blue-700 bg-blue-50 px-2 py-0.5 rounded border border-blue-200">
                            {log.event_type}
                          </span>
                        </td>
                        <td className="py-3 px-4">
                          <div className="font-medium text-slate-900">{log.actor_role}</div>
                          <div className="font-mono text-[10px] text-slate-400">
                            {log.actor_id ? log.actor_id.slice(0, 8) : 'SYSTEM'}
                          </div>
                        </td>
                        <td className="py-3 px-4 max-w-sm">
                          <span className="text-slate-800 line-clamp-1">{log.action_description}</span>
                        </td>
                        <td className="py-3 px-4 font-mono text-[11px] text-slate-600">
                          <div>
                            <span className="text-slate-400">Cur: </span>
                            <span className="font-semibold text-slate-800">{log.current_hash.slice(0, 16)}...</span>
                          </div>
                          <div className="text-[10px] text-slate-400">
                            <span>Prv: </span>
                            <span>{log.prev_record_hash.slice(0, 16)}...</span>
                          </div>
                        </td>
                        <td className="py-3 px-4 font-mono text-slate-500 whitespace-nowrap">
                          {new Date(log.timestamp).toLocaleString()}
                        </td>
                      </tr>

                      {/* Expandable JSON Metadata Drawer */}
                      {isExpanded && (
                        <tr className="bg-slate-50/90 border-b border-slate-200">
                          <td colSpan={7} className="p-4">
                            <div className="rounded-xl border border-slate-200 bg-white p-3 space-y-2">
                              <div className="flex items-center justify-between text-xs font-semibold text-slate-700 border-b border-slate-100 pb-1.5">
                                <span className="flex items-center gap-1.5">
                                  <Database className="w-3.5 h-3.5 text-blue-600" />
                                  Block #{log.id} Immutable Payload (SHA-256 Verified)
                                </span>
                                <span className="font-mono text-[10px] text-slate-400">
                                  Full Current Hash: {log.current_hash}
                                </span>
                              </div>
                              <pre className="font-mono text-[11px] text-slate-800 bg-slate-50 p-2.5 rounded-lg border border-slate-100 overflow-x-auto select-all">
                                {JSON.stringify(log.metadata_json, null, 2)}
                              </pre>
                            </div>
                          </td>
                        </tr>
                      )}
                    </React.Fragment>
                  );
                })}
              </tbody>
            </table>
          </div>
        </GlassCard>
      )}
    </div>
  );
};
