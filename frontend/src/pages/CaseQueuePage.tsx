import React, { useState, useEffect } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { 
  Briefcase, Search, Filter, Plus, ArrowRight, RotateCcw
} from 'lucide-react';
import { GlassCard } from '../components/glass/GlassCard';
import { GlassButton } from '../components/glass/GlassButton';
import { EmptyState } from '../components/common/EmptyState';
import { LoadingSkeleton } from '../components/common/LoadingSkeleton';
import { casesApi } from '../services/api';
import type { Case, CaseStatus, CasePriority } from '../types';

export const CaseQueuePage: React.FC = () => {
  const navigate = useNavigate();

  const [cases, setCases] = useState<Case[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Filters
  const [statusFilter, setStatusFilter] = useState<string>('');
  const [priorityFilter, setPriorityFilter] = useState<string>('');
  const [searchTerm, setSearchTerm] = useState('');

  const fetchCases = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const data = await casesApi.list({
        status: statusFilter || undefined,
        priority: priorityFilter || undefined,
      });
      setCases(data);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to retrieve investigation cases.');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchCases();
  }, [statusFilter, priorityFilter]);

  const filteredCases = cases.filter((c) => {
    if (!searchTerm) return true;
    const term = searchTerm.toLowerCase();
    return (
      c.case_number.toLowerCase().includes(term) ||
      c.summary.toLowerCase().includes(term) ||
      c.screening_id.toLowerCase().includes(term)
    );
  });

  const getStatusBadge = (status: CaseStatus) => {
    switch (status) {
      case 'OPEN':
        return 'bg-blue-50 text-blue-700 border-blue-200';
      case 'IN_REVIEW':
        return 'bg-amber-50 text-amber-700 border-amber-200';
      case 'ESCALATED':
        return 'bg-purple-50 text-purple-700 border-purple-200 font-semibold';
      case 'RESOLVED':
        return 'bg-green-50 text-green-700 border-green-200 font-semibold';
      case 'RETURNED':
        return 'bg-slate-100 text-slate-700 border-slate-300';
      default:
        return 'bg-slate-100 text-slate-700 border-slate-200';
    }
  };

  const getPriorityBadge = (priority: CasePriority) => {
    switch (priority) {
      case 'URGENT':
        return 'text-red-700 bg-red-50 border-red-200 font-bold';
      case 'HIGH':
        return 'text-orange-700 bg-orange-50 border-orange-200 font-semibold';
      case 'MEDIUM':
        return 'text-blue-700 bg-blue-50 border-blue-200';
      case 'LOW':
        return 'text-slate-600 bg-slate-100 border-slate-200';
    }
  };

  return (
    <div className="space-y-6 max-w-7xl mx-auto">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-2 border-b border-slate-200">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-900 flex items-center gap-3">
            Investigation Center
            <span className="text-xs px-2.5 py-0.5 rounded-full bg-blue-50 text-blue-700 border border-blue-200 font-semibold">
              {filteredCases.length} Active Dossiers
            </span>
          </h1>
          <p className="text-sm text-slate-500 mt-1">
            Faceted investigation queue for flagged identity credentials, secondary forensic review, and officer escalation.
          </p>
        </div>
        <div className="flex items-center gap-3">
          <GlassButton
            size="sm"
            variant="ghost"
            onClick={fetchCases}
            icon={<RotateCcw className="w-4 h-4" />}
          >
            Refresh Queue
          </GlassButton>
          <GlassButton
            size="sm"
            variant="primary"
            onClick={() => navigate('/screenings/new')}
            icon={<Plus className="w-4 h-4" />}
          >
            New Screening Intake
          </GlassButton>
        </div>
      </div>

      {error && (
        <div className="p-3 rounded-xl bg-red-50 border border-red-200 text-red-800 text-xs">
          {error}
        </div>
      )}

      {/* Filter & Search Bar */}
      <GlassCard className="p-4">
        <div className="flex flex-col sm:flex-row items-center gap-4">
          {/* Search */}
          <div className="relative flex-1 w-full">
            <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
            <input
              type="text"
              placeholder="Search by case number, screening ID, or summary..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full pl-9 pr-4 py-2 text-xs rounded-xl border border-slate-200 bg-white text-slate-800 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>

          {/* Status Filter */}
          <div className="flex items-center gap-2 w-full sm:w-auto">
            <Filter className="w-4 h-4 text-slate-400 flex-shrink-0" />
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              className="w-full sm:w-auto px-3 py-2 text-xs rounded-xl border border-slate-200 bg-white text-slate-800 focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="">All Statuses</option>
              <option value="OPEN">Open</option>
              <option value="IN_REVIEW">In Review</option>
              <option value="ESCALATED">Escalated</option>
              <option value="RESOLVED">Resolved</option>
              <option value="RETURNED">Returned</option>
            </select>
          </div>

          {/* Priority Filter */}
          <div className="w-full sm:w-auto">
            <select
              value={priorityFilter}
              onChange={(e) => setPriorityFilter(e.target.value)}
              className="w-full sm:w-auto px-3 py-2 text-xs rounded-xl border border-slate-200 bg-white text-slate-800 focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="">All Priorities</option>
              <option value="URGENT">Urgent</option>
              <option value="HIGH">High</option>
              <option value="MEDIUM">Medium</option>
              <option value="LOW">Low</option>
            </select>
          </div>
        </div>
      </GlassCard>

      {/* Case Table */}
      {isLoading ? (
        <div className="space-y-3">
          <LoadingSkeleton className="h-12 w-full" count={5} />
        </div>
      ) : filteredCases.length === 0 ? (
        <EmptyState
          icon={<Briefcase className="w-8 h-8" />}
          title="No Investigation Cases Found"
          description="There are currently no active investigation cases matching the selected filter criteria."
          actionText="Clear Filters"
          onAction={() => {
            setStatusFilter('');
            setPriorityFilter('');
            setSearchTerm('');
          }}
        />
      ) : (
        <GlassCard className="p-0 overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-xs text-left">
              <thead>
                <tr className="border-b border-slate-200 text-slate-500 font-semibold bg-slate-50/70">
                  <th className="py-3 px-4">Case Identifier</th>
                  <th className="py-3 px-4">Status</th>
                  <th className="py-3 px-4">Priority</th>
                  <th className="py-3 px-4">Summary & Notes</th>
                  <th className="py-3 px-4">Opened Timestamp</th>
                  <th className="py-3 px-4 text-right">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {filteredCases.map((c) => (
                  <tr key={c.id} className="hover:bg-slate-50/50 transition">
                    <td className="py-3 px-4">
                      <Link
                        to={`/cases/${c.id}`}
                        className="font-mono font-bold text-blue-700 hover:underline block"
                      >
                        {c.case_number}
                      </Link>
                      <span className="font-mono text-[10px] text-slate-400">
                        Screening: {c.screening_id.slice(0, 8)}...
                      </span>
                    </td>
                    <td className="py-3 px-4">
                      <span className={`px-2.5 py-0.5 rounded-full text-[10px] border ${getStatusBadge(c.status)}`}>
                        {c.status}
                      </span>
                    </td>
                    <td className="py-3 px-4">
                      <span className={`px-2 py-0.5 rounded text-[10px] border ${getPriorityBadge(c.priority)}`}>
                        {c.priority}
                      </span>
                    </td>
                    <td className="py-3 px-4 max-w-md">
                      <div className="font-medium text-slate-900 truncate">{c.summary}</div>
                      <div className="text-[11px] text-slate-500 mt-0.5">
                        {c.notes?.length || 0} officer note(s) logged
                      </div>
                    </td>
                    <td className="py-3 px-4 font-mono text-slate-600">
                      {new Date(c.created_at).toLocaleDateString()}
                    </td>
                    <td className="py-3 px-4 text-right">
                      <GlassButton
                        size="sm"
                        variant="ghost"
                        onClick={() => navigate(`/cases/${c.id}`)}
                        icon={<ArrowRight className="w-3.5 h-3.5" />}
                      >
                        Investigate
                      </GlassButton>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </GlassCard>
      )}
    </div>
  );
};
