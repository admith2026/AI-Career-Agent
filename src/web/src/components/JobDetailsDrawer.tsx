'use client';

import { Badge, MatchScore, SkillBadge, ProgressBar } from '@/components/ui';

interface JobAnalysis {
  match_score: number;
  technologies: string[];
  ai_summary: string | null;
  score_breakdown?: Record<string, number>;
  skill_gaps?: string[];
}

interface Job {
  id: string;
  source: string;
  job_title: string;
  company_name: string | null;
  job_link: string;
  salary_or_rate: string | null;
  location: string | null;
  is_remote: boolean;
  contract_type: string | null;
  date_discovered: string | null;
  description?: string | null;
  analysis?: JobAnalysis | null;
}

interface JobDetailsDrawerProps {
  job: Job;
  onClose: () => void;
  onApply: (jobId: string) => void;
  applying?: boolean;
}

export default function JobDetailsDrawer({ job, onClose, onApply, applying }: JobDetailsDrawerProps) {
  const score = job.analysis?.match_score ?? 0;
  const breakdown = job.analysis?.score_breakdown ?? {};
  const techs = job.analysis?.technologies ?? [];
  const gaps = job.analysis?.skill_gaps ?? [];

  return (
    <>
      {/* Backdrop */}
      <div className="fixed inset-0 bg-black/60 z-40 animate-fade-in" onClick={onClose} />

      {/* Drawer */}
      <div className="fixed right-0 top-0 bottom-0 w-full max-w-lg z-50 bg-navy-900 border-l border-gray-700/30 shadow-2xl flex flex-col animate-slide-in-right overflow-hidden">
        {/* Header */}
        <div className="p-6 border-b border-gray-700/30 bg-navy-900/80 backdrop-blur-sm">
          <div className="flex items-start gap-4">
            <MatchScore score={score} size="lg" />
            <div className="flex-1 min-w-0">
              <h2 className="text-lg font-bold text-white leading-tight">{job.job_title}</h2>
              <p className="text-sm text-gray-400 mt-1">
                {job.company_name || 'Unknown Company'} · {job.location || 'Remote'}
              </p>
              <div className="flex flex-wrap gap-2 mt-2">
                {job.is_remote && <Badge variant="cyan" dot>Remote</Badge>}
                {job.contract_type && <Badge variant="gold">{job.contract_type}</Badge>}
                <Badge variant="gray">{job.source}</Badge>
              </div>
            </div>
            <button
              onClick={onClose}
              className="w-8 h-8 rounded-lg bg-navy-800 flex items-center justify-center text-gray-400 hover:text-white transition-colors flex-shrink-0"
            >
              <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-6 space-y-6">
          {/* Salary */}
          {job.salary_or_rate && (
            <div className="card p-4 flex items-center gap-3">
              <span className="text-2xl">💰</span>
              <div>
                <p className="text-xs text-gray-500 uppercase tracking-wider">Compensation</p>
                <p className="text-lg font-bold text-green-400">{job.salary_or_rate}</p>
              </div>
            </div>
          )}

          {/* AI Match Breakdown */}
          {Object.keys(breakdown).length > 0 && (
            <div className="card p-5">
              <h3 className="text-sm font-semibold text-white mb-3 flex items-center gap-2">
                <svg className="w-4 h-4 text-cyan-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                </svg>
                AI Match Breakdown
              </h3>
              <div className="space-y-3">
                {Object.entries(breakdown).map(([key, val]) => (
                  <div key={key}>
                    <div className="flex justify-between text-sm mb-1">
                      <span className="text-gray-400 capitalize">{key.replace(/_/g, ' ')}</span>
                      <span className="text-white font-medium">{val}%</span>
                    </div>
                    <ProgressBar
                      value={val}
                      max={100}
                      color={val >= 80 ? 'green' : val >= 60 ? 'cyan' : val >= 40 ? 'gold' : 'red'}
                    />
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Tech Stack */}
          {techs.length > 0 && (
            <div className="card p-5">
              <h3 className="text-sm font-semibold text-white mb-3 flex items-center gap-2">
                <svg className="w-4 h-4 text-purple-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 20l4-16m4 4l4 4-4 4M6 16l-4-4 4-4" />
                </svg>
                Tech Stack Required
              </h3>
              <div className="flex flex-wrap gap-1.5">
                {techs.map((t) => (
                  <SkillBadge key={t} name={t} matched={!gaps.includes(t)} />
                ))}
              </div>
            </div>
          )}

          {/* Skill Gaps */}
          {gaps.length > 0 && (
            <div className="card p-5 border-gold-400/20">
              <h3 className="text-sm font-semibold text-gold-400 mb-3 flex items-center gap-2">
                <span className="text-base">⚠️</span>
                Skill Gaps Identified
              </h3>
              <div className="space-y-2">
                {gaps.map((g) => (
                  <div key={g} className="flex items-center gap-2 text-sm">
                    <span className="w-1.5 h-1.5 rounded-full bg-gold-400" />
                    <span className="text-gray-300">{g}</span>
                  </div>
                ))}
              </div>
              <p className="text-xs text-gray-500 mt-3">
                Bridging these gaps could increase your match score by ~10-15%.
              </p>
            </div>
          )}

          {/* AI Summary */}
          {job.analysis?.ai_summary && (
            <div className="card p-5">
              <h3 className="text-sm font-semibold text-white mb-2 flex items-center gap-2">
                <span className="text-base">🤖</span>
                AI Analysis
              </h3>
              <p className="text-sm text-gray-300 leading-relaxed">{job.analysis.ai_summary}</p>
            </div>
          )}

          {/* Job Description */}
          {job.description && (
            <div className="card p-5">
              <h3 className="text-sm font-semibold text-white mb-2">Job Description</h3>
              <p className="text-sm text-gray-400 leading-relaxed whitespace-pre-wrap">{job.description}</p>
            </div>
          )}

          {/* Company / Similar Jobs Placeholder */}
          <div className="card p-5">
            <h3 className="text-sm font-semibold text-white mb-3 flex items-center gap-2">
              <span className="text-base">🏢</span>
              Company Intel
            </h3>
            <div className="grid grid-cols-2 gap-3">
              <div className="bg-navy-950/50 rounded-xl p-3 text-center">
                <p className="text-sm font-bold text-white">{job.company_name || '—'}</p>
                <p className="text-[10px] text-gray-500 mt-0.5">Company</p>
              </div>
              <div className="bg-navy-950/50 rounded-xl p-3 text-center">
                <p className="text-sm font-bold text-white">{job.source}</p>
                <p className="text-[10px] text-gray-500 mt-0.5">Source</p>
              </div>
            </div>
          </div>
        </div>

        {/* Sticky Footer */}
        <div className="p-4 border-t border-gray-700/30 bg-navy-900/80 backdrop-blur-sm flex items-center gap-3">
          <a
            href={job.job_link}
            target="_blank"
            rel="noopener noreferrer"
            className="btn-secondary flex-1 text-sm text-center"
          >
            View Original
          </a>
          <button
            onClick={() => onApply(job.id)}
            disabled={applying}
            className="btn-primary flex-1 text-sm flex items-center justify-center gap-2"
          >
            {applying ? (
              <>
                <svg className="w-4 h-4 animate-spin" viewBox="0 0 24 24" fill="none">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                </svg>
                Applying...
              </>
            ) : (
              <>
                <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7l5 5m0 0l-5 5m5-5H6" />
                </svg>
                Quick Apply
              </>
            )}
          </button>
        </div>
      </div>
    </>
  );
}
