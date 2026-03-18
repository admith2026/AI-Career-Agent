'use client';

import { useEffect, useState } from 'react';
import { marketplaceApi } from '@/lib/api';
import { Badge, LoadingSpinner, StatCard, EmptyState } from '@/components/ui';

interface MarketplaceJob { id: string; title: string; company_name: string; location: string; is_remote: boolean; contract_type: string; salary_min: number | null; salary_max: number | null; required_skills: string[]; experience_level: string; applications_count: number; created_at: string | null; }
interface Candidate { id: string; user_id: string; name: string; email: string; match_score: number; match_reasons: string[]; status: string; }
interface Stats { total_jobs: number; active_jobs: number; total_matches: number; total_recruiters: number; }

export default function MarketplaceView() {
  const [jobs, setJobs] = useState<MarketplaceJob[]>([]);
  const [stats, setStats] = useState<Stats | null>(null);
  const [selectedJob, setSelectedJob] = useState<string | null>(null);
  const [candidates, setCandidates] = useState<Candidate[]>([]);
  const [loading, setLoading] = useState(true);
  const [tab, setTab] = useState<'browse' | 'candidates'>('browse');

  const load = () => {
    setLoading(true);
    Promise.all([
      marketplaceApi.getJobs().then(r => setJobs(r.data.jobs ?? [])).catch(() => {}),
      marketplaceApi.getStats().then(r => setStats(r.data)).catch(() => {}),
    ]).finally(() => setLoading(false));
  };

  useEffect(() => { load(); }, []);

  const viewCandidates = (jobId: string) => {
    setSelectedJob(jobId);
    setTab('candidates');
    marketplaceApi.getCandidates(jobId).then(r => setCandidates(r.data.candidates ?? [])).catch(() => setCandidates([]));
  };

  const matchCandidates = (jobId: string) => {
    marketplaceApi.matchCandidates(jobId).then(() => viewCandidates(jobId));
  };

  const updateCandidate = (matchId: string, status: string) => {
    marketplaceApi.updateCandidateStatus(matchId, status).then(() => {
      if (selectedJob) viewCandidates(selectedJob);
    });
  };

  if (loading) return <LoadingSpinner text="Loading marketplace..." />;

  const EXP_COLORS: Record<string, string> = { junior: 'green', mid: 'blue', senior: 'purple', lead: 'yellow', executive: 'red' };

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="page-title">Job Marketplace</h1>
          <p className="text-gray-400 text-sm mt-1">Recruiter job board, AI-powered candidate matching & hiring</p>
        </div>
        <Badge variant="blue" dot>Marketplace</Badge>
      </div>

      {stats && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <StatCard label="Total Jobs" value={stats.total_jobs} icon="💼" />
          <StatCard label="Active Jobs" value={stats.active_jobs} icon="🟢" />
          <StatCard label="Matches Made" value={stats.total_matches} icon="🤝" />
          <StatCard label="Recruiters" value={stats.total_recruiters} icon="👥" />
        </div>
      )}

      <div className="flex gap-2 border-b border-gray-700/30 pb-2">
        {(['browse', 'candidates'] as const).map(t => (
          <button key={t} onClick={() => setTab(t)}
            className={`px-4 py-2 rounded-t-lg text-sm font-medium transition-all capitalize ${tab === t ? 'bg-blue-500/20 text-blue-400 border-b-2 border-blue-400' : 'text-gray-400 hover:text-white'}`}>
            {t === 'candidates' ? `Candidates${selectedJob ? '' : ' (select job)'}` : t}
          </button>
        ))}
      </div>

      {tab === 'browse' && (
        <div className="space-y-3">
          {jobs.map(j => (
            <div key={j.id} className="glass-card p-5 rounded-xl hover:border-blue-500/50 border border-transparent transition-all cursor-pointer" onClick={() => viewCandidates(j.id)}>
              <div className="flex items-start justify-between">
                <div>
                  <h3 className="text-white font-semibold text-lg">{j.title}</h3>
                  <p className="text-gray-400 text-sm">{j.company_name} • {j.location || 'Remote'}</p>
                </div>
                <div className="flex items-center gap-2">
                  {j.is_remote && <Badge variant="green">Remote</Badge>}
                  <Badge variant={EXP_COLORS[j.experience_level] as any ?? 'gray'}>{j.experience_level}</Badge>
                </div>
              </div>
              <div className="flex flex-wrap gap-1 mt-3">
                {(j.required_skills ?? []).slice(0, 6).map(s => (
                  <span key={s} className="px-2 py-0.5 bg-blue-500/10 text-blue-400 text-xs rounded-full">{s}</span>
                ))}
              </div>
              <div className="flex items-center justify-between mt-3 text-xs text-gray-500">
                <span>{j.contract_type}</span>
                {j.salary_min != null && j.salary_max != null && <span className="text-green-400">${(j.salary_min / 1000).toFixed(0)}k - ${(j.salary_max / 1000).toFixed(0)}k</span>}
                <span>{j.applications_count} applicants</span>
                <button onClick={(e) => { e.stopPropagation(); matchCandidates(j.id); }} className="text-blue-400 hover:text-blue-300">🤖 AI Match</button>
              </div>
            </div>
          ))}
          {jobs.length === 0 && <EmptyState icon="💼" title="No marketplace jobs" description="Jobs posted by recruiters will appear here" />}
        </div>
      )}

      {tab === 'candidates' && (
        <div className="space-y-3">
          {!selectedJob && <EmptyState icon="👤" title="Select a job first" description="Click on a job in Browse to view candidates" />}
          {selectedJob && candidates.length === 0 && (
            <div className="text-center py-8">
              <EmptyState icon="🤖" title="No candidates matched yet" description="Click AI Match on the job to find candidates" />
            </div>
          )}
          {candidates.map(c => (
            <div key={c.id} className="glass-card p-4 rounded-xl flex items-center justify-between">
              <div>
                <h4 className="text-white font-medium">{c.name}</h4>
                <p className="text-gray-400 text-sm">{c.email}</p>
                <div className="flex gap-1 mt-1">
                  {(c.match_reasons ?? []).slice(0, 3).map(r => (
                    <span key={r} className="text-xs px-1.5 py-0.5 bg-green-500/10 text-green-400 rounded">{r}</span>
                  ))}
                </div>
              </div>
              <div className="flex items-center gap-3">
                <div className="text-right">
                  <div className="text-2xl font-bold text-blue-400">{c.match_score}%</div>
                  <Badge variant={c.status === 'hired' ? 'green' : c.status === 'rejected' ? 'red' : 'gray'}>{c.status}</Badge>
                </div>
                <div className="flex flex-col gap-1">
                  <button onClick={() => updateCandidate(c.id, 'shortlisted')} className="text-xs px-2 py-1 bg-blue-600 rounded text-white hover:bg-blue-500">Shortlist</button>
                  <button onClick={() => updateCandidate(c.id, 'contacted')} className="text-xs px-2 py-1 bg-green-600 rounded text-white hover:bg-green-500">Contact</button>
                  <button onClick={() => updateCandidate(c.id, 'rejected')} className="text-xs px-2 py-1 bg-red-600/50 rounded text-gray-300 hover:bg-red-500">Reject</button>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
