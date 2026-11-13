import React from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { 
  FilePlus, ShieldCheck, AlertTriangle, AlertOctagon, 
  Clock, ArrowUpRight, RotateCcw, Activity, Layers, BarChart2
} from 'lucide-react';
import { 
  ResponsiveContainer, PieChart, Pie, Cell, Tooltip as RCTooltip,
  AreaChart, Area, XAxis, YAxis, CartesianGrid, BarChart, Bar
} from 'recharts';
import { useAuth } from '../context/AuthContext';
import { MetricCard } from '../components/common/MetricCard';
import { RiskBadge } from '../components/common/RiskBadge';
import { GlassCard } from '../components/glass/GlassCard';
import { GlassButton } from '../components/glass/GlassButton';
import { LoadingSkeleton } from '../components/common/LoadingSkeleton';
import { dashboardApi } from '../services/api';

export const DashboardPage: React.FC = () => {
  const { user } = useAuth();
  const navigate = useNavigate();

  const { data, isLoading, refetch } = useQuery({
    queryKey: ['dashboard-stats'],
    queryFn: () => dashboardApi.getStats(),
    refetchInterval: 10000, // Live poll every 10s
  });

  if (isLoading) {
    return (
      <div className="space-y-6 max-w-7xl mx-auto">
        <LoadingSkeleton className="h-24 w-full" />
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          <LoadingSkeleton className="h-28 w-full" count={4} />
        </div>
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <LoadingSkeleton className="h-72 w-full" />
          <LoadingSkeleton className="h-72 w-full" />
        </div>
      </div>
    );
  }

  const metrics = data?.metrics || {
    total_screenings: 0,
    today_screenings: 0,
    clear_count: 0,
    review_count: 0,
    high_risk_count: 0,
    active_cases: 0,
    resolved_cases: 0,
    avg_latency_ms: 1180,
  };

  const charts = data?.charts || {
    risk_distribution: [],
    doc_type_distribution: [],
    detection_methods: [],
    temporal_volume: [],
  };

  const recent = data?.recent_activity || [];

  return (
    <div className="space-y-6 max-w-7xl mx-auto">
      {/* Welcome & Command Status Banner */}
      <GlassCard className="flex flex-col md:flex-row md:items-center justify-between gap-4 p-6 border-blue-200/80 bg-gradient-to-r from-blue-50/70 via-white to-slate-50 shadow-xs">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="text-xs font-mono text-blue-700 font-semibold uppercase tracking-wider">
              Border Security Terminal Active
            </span>
            <span className="w-2 h-2 rounded-full bg-green-500 animate-pulse" />
          </div>
          <h1 className="text-xl font-bold text-slate-900 tracking-tight">
            Security Command Center // {user?.full_name}
          </h1>
          <p className="text-xs text-slate-600 mt-1 max-w-2xl leading-relaxed">
            Role: <span className="text-blue-700 font-mono font-semibold">{user?.role?.replace('_', ' ')}</span> • 
            Status: <span className="text-emerald-700 font-mono font-medium">Authenticated</span> • 
            Live database sync: <span className="text-slate-800 font-mono font-semibold">{metrics.total_screenings} total credentials tracked</span>.
          </p>
        </div>

        <div className="flex items-center gap-3 shrink-0">
          <GlassButton
            variant="ghost"
            size="sm"
            icon={<RotateCcw className="w-4 h-4" />}
            onClick={() => refetch()}
          >
            Refresh
          </GlassButton>
          <GlassButton
            variant="primary"
            size="md"
            icon={<FilePlus className="w-4 h-4" />}
            onClick={() => navigate('/screenings/new')}
          >
            Initiate Screening
          </GlassButton>
        </div>
      </GlassCard>

      {/* Top Level Metric KPIs from DB */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <MetricCard
          title="Total Credential Intakes"
          value={String(metrics.total_screenings)}
          subtitle="All recorded submissions in ledger"
          icon={<Clock className="w-4 h-4 text-blue-600" />}
          trend={{ value: `${metrics.today_screenings} today`, isPositive: true }}
          isSynthetic={false}
        />
        <MetricCard
          title="CLEAR Verifications"
          value={String(metrics.clear_count)}
          subtitle="Passed all deterministic criteria"
          icon={<ShieldCheck className="w-4 h-4 text-emerald-600" />}
          trend={{ 
            value: metrics.total_screenings > 0 
              ? `${((metrics.clear_count / metrics.total_screenings) * 100).toFixed(1)}% rate` 
              : '100% rate', 
            isPositive: true 
          }}
          isSynthetic={false}
        />
        <MetricCard
          title="Manual Review Queue"
          value={String(metrics.review_count)}
          subtitle="Flagged for secondary inspection"
          icon={<AlertTriangle className="w-4 h-4 text-amber-600" />}
          trend={{ value: `${metrics.active_cases} active cases`, isPositive: false }}
          isSynthetic={false}
        />
        <MetricCard
          title="High Risk Anomalies"
          value={String(metrics.high_risk_count)}
          subtitle="Cryptographic / Forensic alerts"
          icon={<AlertOctagon className="w-4 h-4 text-red-600" />}
          trend={{ 
            value: metrics.total_screenings > 0 
              ? `${((metrics.high_risk_count / metrics.total_screenings) * 100).toFixed(1)}% anomaly` 
              : '0% anomaly', 
            isPositive: false 
          }}
          isSynthetic={false}
        />
      </div>

      {/* 4 Interactive Visualizations Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Temporal Volume Chart */}
        <GlassCard className="p-5 space-y-3">
          <div className="flex items-center justify-between border-b border-slate-200 pb-2">
            <div>
              <h3 className="text-sm font-bold text-slate-900 flex items-center gap-1.5">
                <BarChart2 className="w-4 h-4 text-blue-600" />
                Screening Volume (Past 7 Days)
              </h3>
              <p className="text-[11px] text-slate-500">Daily intake trend across border checkpoints</p>
            </div>
            <span className="text-[11px] font-mono text-slate-500">Live DB Stream</span>
          </div>

          <div className="h-56 w-full pt-2">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={charts.temporal_volume} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                <defs>
                  <linearGradient id="volGradient" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#2563EB" stopOpacity={0.25} />
                    <stop offset="95%" stopColor="#2563EB" stopOpacity={0.0} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="#E2E8F0" />
                <XAxis dataKey="date" tick={{ fontSize: 10, fill: '#64748B' }} />
                <YAxis allowDecimals={false} tick={{ fontSize: 10, fill: '#64748B' }} />
                <RCTooltip 
                  contentStyle={{ backgroundColor: '#FFFFFF', borderColor: '#E2E8F0', borderRadius: '8px', fontSize: '11px' }} 
                />
                <Area type="monotone" dataKey="screenings" stroke="#2563EB" strokeWidth={2} fillOpacity={1} fill="url(#volGradient)" />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </GlassCard>

        {/* Risk Distribution Chart */}
        <GlassCard className="p-5 space-y-3">
          <div className="flex items-center justify-between border-b border-slate-200 pb-2">
            <div>
              <h3 className="text-sm font-bold text-slate-900 flex items-center gap-1.5">
                <ShieldCheck className="w-4 h-4 text-blue-600" />
                Risk Classification Breakdown
              </h3>
              <p className="text-[11px] text-slate-500">Deterministic risk levels across audited documents</p>
            </div>
            <span className="text-[11px] font-mono text-slate-500">3-Tier Matrix</span>
          </div>

          <div className="h-56 w-full flex items-center justify-center pt-2">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={charts.risk_distribution}
                  dataKey="count"
                  nameKey="name"
                  cx="50%"
                  cy="50%"
                  innerRadius={50}
                  outerRadius={75}
                  paddingAngle={4}
                  label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                >
                  {charts.risk_distribution.map((entry: any, index: number) => (
                    <Cell key={`cell-${index}`} fill={entry.color || '#2563EB'} />
                  ))}
                </Pie>
                <RCTooltip contentStyle={{ backgroundColor: '#FFFFFF', borderColor: '#E2E8F0', borderRadius: '8px', fontSize: '11px' }} />
              </PieChart>
            </ResponsiveContainer>
          </div>
        </GlassCard>

        {/* Document Specification Breakdown */}
        <GlassCard className="p-5 space-y-3">
          <div className="flex items-center justify-between border-b border-slate-200 pb-2">
            <div>
              <h3 className="text-sm font-bold text-slate-900 flex items-center gap-1.5">
                <Layers className="w-4 h-4 text-blue-600" />
                Supported Document Specifications
              </h3>
              <p className="text-[11px] text-slate-500">Intake volume by ICAO template specification</p>
            </div>
            <span className="text-[11px] font-mono text-slate-500">ICAO 9303</span>
          </div>

          <div className="h-52 w-full pt-2">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={charts.doc_type_distribution} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#E2E8F0" />
                <XAxis dataKey="type" tick={{ fontSize: 10, fill: '#64748B' }} />
                <YAxis allowDecimals={false} tick={{ fontSize: 10, fill: '#64748B' }} />
                <RCTooltip contentStyle={{ backgroundColor: '#FFFFFF', borderColor: '#E2E8F0', borderRadius: '8px', fontSize: '11px' }} />
                <Bar dataKey="count" fill="#3B82F6" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </GlassCard>

        {/* Forensic Detection Anomaly Categories */}
        <GlassCard className="p-5 space-y-3">
          <div className="flex items-center justify-between border-b border-slate-200 pb-2">
            <div>
              <h3 className="text-sm font-bold text-slate-900 flex items-center gap-1.5">
                <Activity className="w-4 h-4 text-blue-600" />
                Forensic Detection Method Telemetry
              </h3>
              <p className="text-[11px] text-slate-500">Anomalies identified across the 5 forensic inspection pillars</p>
            </div>
            <span className="text-[11px] font-mono text-slate-500">Multi-Factor</span>
          </div>

          <div className="h-52 w-full pt-2">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={charts.detection_methods} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#E2E8F0" />
                <XAxis dataKey="method" tick={{ fontSize: 10, fill: '#64748B' }} />
                <YAxis allowDecimals={false} tick={{ fontSize: 10, fill: '#64748B' }} />
                <RCTooltip contentStyle={{ backgroundColor: '#FFFFFF', borderColor: '#E2E8F0', borderRadius: '8px', fontSize: '11px' }} />
                <Bar dataKey="anomalies" fill="#F59E0B" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </GlassCard>
      </div>

      {/* Live Screening Stream & Recent Activity */}
      <GlassCard className="p-0 overflow-hidden shadow-xs">
        <div className="flex items-center justify-between p-4 border-b border-slate-200 bg-slate-50/50">
          <div>
            <h3 className="text-sm font-bold text-slate-900">Recent Screening Submissions</h3>
            <p className="text-xs text-slate-500">Click any dossier to inspect OCR fields, MRZ verification, or forensic heatmap</p>
          </div>
          <GlassButton
            variant="ghost"
            size="sm"
            onClick={() => navigate('/cases')}
            icon={<ArrowUpRight className="w-3.5 h-3.5" />}
          >
            Investigation Queue
          </GlassButton>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-xs text-left">
            <thead>
              <tr className="border-b border-slate-200 text-slate-500 font-semibold bg-slate-50/70">
                <th className="py-2.5 px-4">Reference Code</th>
                <th className="py-2.5 px-4">Template Spec</th>
                <th className="py-2.5 px-4">Issuing State</th>
                <th className="py-2.5 px-4">Risk Level</th>
                <th className="py-2.5 px-4">Score</th>
                <th className="py-2.5 px-4">Classification Mode</th>
                <th className="py-2.5 px-4">Ingestion Time</th>
                <th className="py-2.5 px-4 text-right">Inspect</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {recent.map((s: any) => (
                <tr key={s.id} className="hover:bg-slate-50/60 transition">
                  <td className="py-3 px-4 font-mono font-bold text-blue-700">
                    <Link to={`/screenings/${s.id}/quality`} className="hover:underline">
                      {s.reference_no}
                    </Link>
                  </td>
                  <td className="py-3 px-4 font-mono text-slate-800">{s.document_type}</td>
                  <td className="py-3 px-4 font-mono text-slate-600">{s.country}</td>
                  <td className="py-3 px-4">
                    <RiskBadge level={s.risk_level} size="sm" />
                  </td>
                  <td className="py-3 px-4 font-mono font-bold text-slate-800">
                    {s.risk_score?.toFixed(0)}/100
                  </td>
                  <td className="py-3 px-4">
                    {s.is_synthetic ? (
                      <span className="px-2 py-0.5 rounded text-[10px] font-mono font-medium bg-purple-50 text-purple-700 border border-purple-200">
                        SYNTHETIC DEMO
                      </span>
                    ) : (
                      <span className="px-2 py-0.5 rounded text-[10px] font-mono font-medium bg-blue-50 text-blue-700 border border-blue-200">
                        PRODUCTION
                      </span>
                    )}
                  </td>
                  <td className="py-3 px-4 font-mono text-slate-500">
                    {new Date(s.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' })}
                  </td>
                  <td className="py-3 px-4 text-right">
                    <GlassButton
                      size="sm"
                      variant="ghost"
                      onClick={() => navigate(`/screenings/${s.id}/quality`)}
                    >
                      Inspect &rarr;
                    </GlassButton>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </GlassCard>
    </div>
  );
};
