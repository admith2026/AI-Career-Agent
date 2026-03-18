'use client';

import { useEffect, useState } from 'react';
import { jobsApi, applicationsApi, decisionsApi, graphApi, pipelineApi, agentsApi } from '@/lib/api';
import { StatCard, MatchScore, Badge, ProgressBar, LoadingSpinner } from '@/components/ui';

interface Stats {
  totalJobs: number;
  activeJobs: number;
  bySource: Record<string, number>;
  totalApplications: number;
  appsByStatus: Record<string, number>;
}

interface DashboardProps {
  onNavigate?: (view: 'dashboard' | 'jobs' | 'applications' | 'resumes' | 'signals' | 'recruiters' | 'pipeline' | 'graph' | 'decisions' | 'analytics' | 'skills') => void;
}

export default function Dashboard({ onNavigate }: DashboardProps) {
  const [stats, setStats] = useState<Stats | null>(null);
  const [recentJobs, setRecentJobs] = useState<any[]>([]);
  const [decisionStats, setDecisionStats] = useState<any>(null);
  const [graphStats, setGraphStats] = useState<any>(null);
  const [agentActivity, setAgentActivity] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchAll = async () => {
      try {
        const [jobRes, appRes, jobsRes, decRes, gRes] = await Promise.all([
          jobsApi.getStats().catch(() => ({ data: {} })),
          applicationsApi.getStats().catch(() => ({ data: {} })),
          jobsApi.getJobs({ page: 1, pageSize: 5 }).catch(() => ({ data: { data: [] } })),
          decisionsApi.getStats().catch(() => ({ data: {} })),
          graphApi.getStats().catch(() => ({ data: {} })),
        ]);
        setStats({
          totalJobs: jobRes.data.total ?? 0,
          activeJobs: jobRes.data.active ?? 0,
          bySource: jobRes.data.by_source ?? {},
          totalApplications: appRes.data.total ?? 0,
          appsByStatus: appRes.data.by_status ?? {},
        });
        setRecentJobs(jobsRes.data?.data ?? []);
        setDecisionStats(decRes.data);
        setGraphStats(gRes.data);
        // Load agent activity feed
        agentsApi.getActivity(10).then(r => setAgentActivity(r.data?.activity ?? [])).catch(() => {});
      } catch {
        setStats({ totalJobs: 0, activeJobs: 0, bySource: {}, totalApplications: 0, appsByStatus: {} });
      } finally {
        setLoading(false);
      }
    };
    fetchAll();
  }, []);

  if (loading) return <LoadingSpinner text="Loading dashboard..." />;

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="page-title">Dashboard</h1>
          <p className="text-gray-400 text-sm mt-1">Your career intelligence at a glance</p>
        </div>
        <div className="flex items-center gap-2">
          <span className="badge-cyan">
            <span className="w-2 h-2 rounded-full bg-cyan-400 animate-pulse mr-1.5" />
            System Active
          </span>
        </div>
      </div>

      {/* Stat Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          label="Jobs Discovered"
          value={stats?.totalJobs ?? 0}
          accent="cyan"
          icon={<svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M21 13.255A23.931 23.931 0 0112 15c-3.183 0-6.22-.62-9-1.745M16 6V4a2 2 0 00-2-2h-4a2 2 0 00-2 2v2m4 6h.01M5 20h14a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" /></svg>}
        />
        <StatCard
          label="Active Jobs"
          value={stats?.activeJobs ?? 0}
          accent="green"
          icon={<svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>}
        />
        <StatCard
          label="Applications"
          value={stats?.totalApplications ?? 0}
          accent="purple"
          icon={<svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" /></svg>}
        />
        <StatCard
          label="Interviews"
          value={stats?.appsByStatus?.['interview'] ?? 0}
          accent="gold"
          icon={<svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" /></svg>}
        />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Recent AI Job Feed */}
        <div className="lg:col-span-2 card p-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="section-title">Latest Job Matches</h2>
            {onNavigate && (
              <button onClick={() => onNavigate('jobs')} className="text-cyan-400 text-sm font-medium hover:text-cyan-300 transition-colors">
                View all →
              </button>
            )}
          </div>
          {recentJobs.length === 0 ? (
            <p className="text-gray-500 text-sm py-8 text-center">No jobs discovered yet. Crawlers will start automatically.</p>
          ) : (
            <div className="space-y-3">
              {recentJobs.map((job: any) => (
                <div key={job.id} className="flex items-center gap-4 p-3 rounded-xl bg-navy-950/50 hover:bg-navy-950 transition-colors group">
                  <MatchScore score={job.analysis?.match_score ?? 0} size="sm" showLabel={false} />
                  <div className="flex-1 min-w-0">
                    <h3 className="text-sm font-medium text-white truncate group-hover:text-cyan-400 transition-colors">{job.job_title}</h3>
                    <p className="text-xs text-gray-500 truncate">{job.company_name || 'Unknown'} · {job.location || 'Remote'}</p>
                  </div>
                  <div className="flex items-center gap-2">
                    {job.salary_or_rate && <span className="text-xs text-green-400 font-medium">{job.salary_or_rate}</span>}
                    <Badge variant={job.is_remote ? 'cyan' : 'gray'}>{job.is_remote ? 'Remote' : 'On-site'}</Badge>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Quick Stats Column */}
        <div className="space-y-6">
          {/* Application Status */}
          <div className="card p-6">
            <h2 className="section-title mb-4">Application Pipeline</h2>
            <div className="space-y-3">
              {['pending', 'applied', 'interview', 'offered', 'rejected'].map((status) => {
                const count = stats?.appsByStatus?.[status] ?? 0;
                const total = stats?.totalApplications || 1;
                const colorMap: Record<string, 'gold' | 'cyan' | 'purple' | 'green' | 'red'> = {
                  pending: 'gold', applied: 'cyan', interview: 'purple', offered: 'green', rejected: 'red',
                };
                return (
                  <div key={status}>
                    <div className="flex justify-between text-sm mb-1">
                      <span className="text-gray-400 capitalize">{status}</span>
                      <span className="text-white font-medium">{count}</span>
                    </div>
                    <ProgressBar value={count} max={total} color={colorMap[status]} />
                  </div>
                );
              })}
            </div>
          </div>

          {/* Decision Engine */}
          <div className="card p-6">
            <h2 className="section-title mb-4">AI Decisions</h2>
            <div className="grid grid-cols-2 gap-3">
              <div className="bg-navy-950/50 rounded-xl p-3 text-center">
                <p className="text-xl font-bold text-white">{decisionStats?.total_decisions ?? 0}</p>
                <p className="text-[10px] text-gray-500 uppercase tracking-wider mt-1">Total</p>
              </div>
              <div className="bg-navy-950/50 rounded-xl p-3 text-center">
                <p className="text-xl font-bold text-cyan-400">{decisionStats?.executed ?? 0}</p>
                <p className="text-[10px] text-gray-500 uppercase tracking-wider mt-1">Executed</p>
              </div>
              {Object.entries((decisionStats?.by_decision as Record<string, number>) ?? {}).slice(0, 2).map(([d, c]) => (
                <div key={d} className="bg-navy-950/50 rounded-xl p-3 text-center">
                  <p className="text-xl font-bold text-gold-400">{typeof c === 'object' ? JSON.stringify(c) : c}</p>
                  <p className="text-[10px] text-gray-500 uppercase tracking-wider mt-1">{d.replace(/_/g, ' ')}</p>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* Bottom row: Sources + Knowledge Graph */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Jobs by Source */}
        <div className="card p-6">
          <h2 className="section-title mb-4">Jobs by Source</h2>
          <div className="space-y-3">
            {Object.entries(stats?.bySource ?? {}).map(([source, count]) => {
              const maxCount = Math.max(...Object.values(stats?.bySource ?? { _: 1 }), 1);
              return (
                <div key={source} className="flex items-center gap-3">
                  <span className="text-sm text-gray-300 w-32 truncate">{source}</span>
                  <div className="flex-1">
                    <ProgressBar value={count} max={maxCount} color="cyan" height="md" />
                  </div>
                  <span className="text-sm text-white font-medium w-10 text-right">{typeof count === 'object' ? JSON.stringify(count) : count}</span>
                </div>
              );
            })}
            {Object.keys(stats?.bySource ?? {}).length === 0 && (
              <p className="text-gray-500 text-sm text-center py-4">No jobs discovered yet.</p>
            )}
          </div>
        </div>

        {/* Knowledge Graph Stats */}
        <div className="card p-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="section-title">Knowledge Graph</h2>
            {onNavigate && (
              <button onClick={() => onNavigate('graph')} className="text-cyan-400 text-sm font-medium hover:text-cyan-300 transition-colors">
                Explore →
              </button>
            )}
          </div>
          <div className="grid grid-cols-3 gap-3">
            {[
              { label: 'Companies', value: graphStats?.company_count ?? 0, icon: '🏢' },
              { label: 'Recruiters', value: graphStats?.recruiter_count ?? 0, icon: '👤' },
              { label: 'Technologies', value: graphStats?.technology_count ?? 0, icon: '⚡' },
              { label: 'Job Roles', value: graphStats?.jobrole_count ?? 0, icon: '💼' },
              { label: 'Signals', value: graphStats?.hiringsignal_count ?? 0, icon: '📡' },
              { label: 'Relations', value: graphStats?.total_relationships ?? 0, icon: '🔗' },
            ].map((item) => (
              <div key={item.label} className="bg-navy-950/50 rounded-xl p-3 text-center hover:bg-navy-950 transition-colors">
                <span className="text-lg">{item.icon}</span>
                <p className="text-lg font-bold text-white mt-1">{item.value}</p>
                <p className="text-[10px] text-gray-500 uppercase tracking-wider">{item.label}</p>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Agent Activity Feed */}
      {agentActivity.length > 0 && (
        <div className="card p-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="section-title">🤖 Agent Activity</h2>
            {onNavigate && (
              <button onClick={() => onNavigate('pipeline')} className="text-cyan-400 text-sm font-medium hover:text-cyan-300 transition-colors">
                View all →
              </button>
            )}
          </div>
          <div className="space-y-2">
            {agentActivity.slice(0, 8).map((item: any, i: number) => (
              <div key={i} className="flex items-center gap-3 p-2 rounded-lg bg-navy-950/50 hover:bg-navy-950 transition-colors">
                <span className="text-sm">
                  {item.type === 'task' ? '⚙️' : item.type === 'application' ? '📝' : '🤖'}
                </span>
                <div className="flex-1 min-w-0">
                  <p className="text-xs text-white truncate">{item.description || item.title || `${item.type} event`}</p>
                </div>
                {item.status && (
                  <span className={`text-[10px] px-1.5 py-0.5 rounded ${
                    item.status === 'completed' ? 'bg-green-400/10 text-green-400' :
                    item.status === 'failed' ? 'bg-red-400/10 text-red-400' :
                    'bg-gray-700 text-gray-400'
                  }`}>{item.status}</span>
                )}
                <span className="text-[10px] text-gray-600">{item.timestamp ? new Date(item.timestamp).toLocaleTimeString() : ''}</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
