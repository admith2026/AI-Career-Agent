'use client';

import { useEffect, useState } from 'react';
import { applicationsApi } from '@/lib/api';
import { useAuthStore } from '@/lib/store';
import { Badge, LoadingSpinner, EmptyState, ProgressBar } from '@/components/ui';

interface Application {
  id: string;
  job_id: string;
  status: string;
  applied_via: string | null;
  applied_at: string | null;
  notes: string | null;
  created_at: string | null;
  job?: {
    job_title: string;
    company_name: string | null;
    source: string;
    job_link: string;
  } | null;
}

const statusFlow = ['pending', 'applied', 'interview', 'offered', 'rejected'];

const statusConfig: Record<string, { variant: 'gold' | 'cyan' | 'purple' | 'green' | 'red'; icon: string }> = {
  pending: { variant: 'gold', icon: '⏳' },
  applied: { variant: 'cyan', icon: '📨' },
  interview: { variant: 'purple', icon: '🎯' },
  offered: { variant: 'green', icon: '🎉' },
  rejected: { variant: 'red', icon: '✗' },
};

export default function Applications() {
  const { user } = useAuthStore();
  const [apps, setApps] = useState<Application[]>([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState('');
  const [view, setView] = useState<'table' | 'timeline'>('table');

  useEffect(() => {
    if (!user) return;
    applicationsApi.getUserApplications()
      .then((res) => setApps(Array.isArray(res.data) ? res.data : (Array.isArray(res.data?.data) ? res.data.data : [])))
      .catch(() => setApps([]))
      .finally(() => setLoading(false));
  }, [user]);

  const filtered = filter ? apps.filter((a) => a.status === filter) : apps;

  // Stats
  const statusCounts = statusFlow.reduce((acc, s) => {
    acc[s] = apps.filter((a) => a.status === s).length;
    return acc;
  }, {} as Record<string, number>);

  if (loading) return <LoadingSpinner text="Loading applications..." />;

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="page-title">Application Tracker</h1>
          <p className="text-gray-400 text-sm mt-1">{apps.length} total applications</p>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={() => setView('table')}
            className={`p-2 rounded-lg transition-all ${view === 'table' ? 'bg-cyan-400/10 text-cyan-400' : 'text-gray-500 hover:text-gray-300'}`}
            title="Table View"
          >
            <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M3 10h18M3 14h18m-9-4v8m-7 0h14a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z" />
            </svg>
          </button>
          <button
            onClick={() => setView('timeline')}
            className={`p-2 rounded-lg transition-all ${view === 'timeline' ? 'bg-cyan-400/10 text-cyan-400' : 'text-gray-500 hover:text-gray-300'}`}
            title="Timeline View"
          >
            <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          </button>
        </div>
      </div>

      {/* Pipeline Overview */}
      <div className="card p-6">
        <h2 className="section-title mb-4">Pipeline Overview</h2>
        <div className="flex items-center gap-2">
          {statusFlow.map((status, i) => {
            const count = statusCounts[status] || 0;
            const cfg = statusConfig[status];
            const isActive = !filter || filter === status;
            return (
              <button
                key={status}
                onClick={() => setFilter(filter === status ? '' : status)}
                className={`flex-1 card p-3 text-center cursor-pointer transition-all ${
                  isActive ? 'border-gray-600/50' : 'opacity-40'
                } ${filter === status ? 'ring-1 ring-cyan-400/30 shadow-glow' : ''}`}
              >
                <span className="text-lg">{cfg.icon}</span>
                <p className="text-xl font-bold text-white mt-1">{count}</p>
                <p className="text-[10px] text-gray-500 uppercase tracking-wider capitalize">{status}</p>
              </button>
            );
          })}
        </div>
      </div>

      {/* Status Filter Pills */}
      <div className="flex gap-2 flex-wrap">
        <button
          onClick={() => setFilter('')}
          className={`px-3 py-1.5 rounded-xl text-xs font-medium transition-all ${
            filter === '' ? 'bg-cyan-400/10 text-cyan-400 border border-cyan-400/30' : 'bg-surface text-gray-400 border border-transparent'
          }`}
        >
          All ({apps.length})
        </button>
        {statusFlow.map((s) => (
          <button
            key={s}
            onClick={() => setFilter(filter === s ? '' : s)}
            className={`px-3 py-1.5 rounded-xl text-xs font-medium transition-all capitalize ${
              filter === s ? 'bg-cyan-400/10 text-cyan-400 border border-cyan-400/30' : 'bg-surface text-gray-400 border border-transparent'
            }`}
          >
            {s} ({statusCounts[s] ?? 0})
          </button>
        ))}
      </div>

      {/* Application List */}
      {filtered.length === 0 ? (
        <EmptyState
          icon="📝"
          title="No applications found"
          description="Apply to jobs from the Job Feed to start tracking your applications here."
        />
      ) : view === 'table' ? (
        /* Table View */
        <div className="card overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b border-gray-700/30">
                  <th className="text-left text-xs text-gray-500 uppercase tracking-wider font-medium px-5 py-3">Position</th>
                  <th className="text-left text-xs text-gray-500 uppercase tracking-wider font-medium px-5 py-3">Company</th>
                  <th className="text-left text-xs text-gray-500 uppercase tracking-wider font-medium px-5 py-3">Source</th>
                  <th className="text-left text-xs text-gray-500 uppercase tracking-wider font-medium px-5 py-3">Status</th>
                  <th className="text-left text-xs text-gray-500 uppercase tracking-wider font-medium px-5 py-3">Applied</th>
                  <th className="text-left text-xs text-gray-500 uppercase tracking-wider font-medium px-5 py-3">Actions</th>
                </tr>
              </thead>
              <tbody>
                {filtered.map((app, i) => {
                  const cfg = statusConfig[app.status] || statusConfig.pending;
                  return (
                    <tr
                      key={app.id}
                      className="border-b border-gray-700/20 hover:bg-navy-950/50 transition-colors animate-slide-up"
                      style={{ animationDelay: `${i * 20}ms` }}
                    >
                      <td className="px-5 py-4">
                        <span className="text-sm font-medium text-white">{app.job?.job_title || 'Unknown'}</span>
                      </td>
                      <td className="px-5 py-4">
                        <span className="text-sm text-gray-400">{app.job?.company_name || 'Unknown'}</span>
                      </td>
                      <td className="px-5 py-4">
                        <Badge variant="gray">{app.job?.source || 'N/A'}</Badge>
                      </td>
                      <td className="px-5 py-4">
                        <Badge variant={cfg.variant}>{cfg.icon} {app.status}</Badge>
                      </td>
                      <td className="px-5 py-4">
                        <span className="text-xs text-gray-500">
                          {app.applied_at ? new Date(app.applied_at).toLocaleDateString() : app.created_at ? new Date(app.created_at).toLocaleDateString() : '—'}
                        </span>
                      </td>
                      <td className="px-5 py-4">
                        {app.job?.job_link && (
                          <a
                            href={app.job.job_link}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="text-cyan-400 text-sm hover:text-cyan-300 transition-colors"
                          >
                            View →
                          </a>
                        )}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>
      ) : (
        /* Timeline View */
        <div className="space-y-4">
          {filtered.map((app, i) => {
            const cfg = statusConfig[app.status] || statusConfig.pending;
            const statusIndex = statusFlow.indexOf(app.status);
            return (
              <div
                key={app.id}
                className="card-hover p-5 animate-slide-up"
                style={{ animationDelay: `${i * 30}ms` }}
              >
                <div className="flex items-start gap-4">
                  {/* Timeline dot */}
                  <div className="flex flex-col items-center gap-1 pt-1">
                    <div className={`w-3 h-3 rounded-full ${
                      app.status === 'offered' ? 'bg-green-400' :
                      app.status === 'rejected' ? 'bg-red-400' :
                      app.status === 'interview' ? 'bg-purple-400' :
                      'bg-cyan-400'
                    }`} />
                    {i < filtered.length - 1 && <div className="w-0.5 h-12 bg-gray-700/50" />}
                  </div>

                  <div className="flex-1">
                    <div className="flex items-center justify-between">
                      <div>
                        <h3 className="text-sm font-semibold text-white">{app.job?.job_title || 'Unknown'}</h3>
                        <p className="text-xs text-gray-500 mt-0.5">
                          {app.job?.company_name || 'Unknown'} · {app.applied_via ? `via ${app.applied_via}` : 'Direct'}
                        </p>
                      </div>
                      <Badge variant={cfg.variant}>{cfg.icon} {app.status}</Badge>
                    </div>

                    {/* Progress */}
                    <div className="mt-3">
                      <div className="flex gap-1">
                        {statusFlow.slice(0, -1).map((s, j) => (
                          <div
                            key={s}
                            className={`flex-1 h-1 rounded-full ${
                              j <= statusIndex && app.status !== 'rejected'
                                ? 'bg-cyan-400'
                                : app.status === 'rejected' && j <= statusIndex
                                ? 'bg-red-400'
                                : 'bg-gray-700/50'
                            }`}
                          />
                        ))}
                      </div>
                    </div>

                    {/* AI Follow-up Suggestion */}
                    {app.status === 'applied' && (
                      <div className="mt-3 p-2.5 rounded-xl bg-gold-400/5 border border-gold-400/10">
                        <p className="text-xs text-gold-400 font-medium">
                          💡 AI Suggestion: Follow up in 3-5 days if no response
                        </p>
                      </div>
                    )}
                    {app.status === 'interview' && (
                      <div className="mt-3 p-2.5 rounded-xl bg-purple-400/5 border border-purple-400/10">
                        <p className="text-xs text-purple-400 font-medium">
                          🎯 AI Suggestion: Prepare tech interview materials for this role
                        </p>
                      </div>
                    )}

                    {app.notes && <p className="text-xs text-gray-500 mt-2">{app.notes}</p>}
                    <p className="text-[10px] text-gray-600 mt-2">
                      {app.applied_at ? new Date(app.applied_at).toLocaleString() : app.created_at ? new Date(app.created_at).toLocaleString() : ''}
                    </p>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
