'use client';

import { useEffect, useState } from 'react';
import { decisionsApi } from '@/lib/api';
import { useAuthStore } from '@/lib/store';
import { StatCard, Badge, EmptyState, LoadingSpinner } from '@/components/ui';

interface Decision {
  id: string;
  job_id: string | null;
  decision_type: string;
  decision: string;
  reason: string | null;
  score_data: { score?: number; breakdown?: Record<string, number> } | null;
  executed: boolean;
  created_at: string;
}

interface DecisionStats {
  total_decisions: number;
  executed: number;
  by_decision: Record<string, number>;
}

const decisionConfig: Record<string, { variant: 'green' | 'blue' | 'gold' | 'gray' | 'cyan' | 'purple'; icon: string }> = {
  auto_apply: { variant: 'green', icon: '🚀' },
  recommend_apply: { variant: 'cyan', icon: '👍' },
  outreach: { variant: 'gold', icon: '📧' },
  skip: { variant: 'gray', icon: '⏭️' },
};

export default function DecisionLog() {
  const { user } = useAuthStore();
  const [decisions, setDecisions] = useState<Decision[]>([]);
  const [stats, setStats] = useState<DecisionStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [evaluating, setEvaluating] = useState(false);
  const [filter, setFilter] = useState<string | null>(null);

  const fetchData = () => {
    Promise.all([
      decisionsApi.getLog(100).catch(() => ({ data: [] })),
      decisionsApi.getStats().catch(() => ({ data: {} })),
    ]).then(([dRes, sRes]) => {
      const dData = dRes.data;
      setDecisions(Array.isArray(dData) ? dData : (Array.isArray(dData?.decisions) ? dData.decisions : []));
      setStats(sRes.data);
      setLoading(false);
    });
  };

  useEffect(() => { fetchData(); }, []);

  const handleBatchEvaluate = async () => {
    if (!user?.id) return;
    setEvaluating(true);
    try {
      await decisionsApi.batchEvaluate(user.id, 50);
      fetchData();
    } catch {
      alert('Batch evaluation failed');
    } finally {
      setEvaluating(false);
    }
  };

  const filtered = filter ? decisions.filter(d => d.decision === filter) : decisions;

  if (loading) return <LoadingSpinner text="Loading decisions..." />;

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="page-title">Decision Log</h1>
          <p className="text-gray-400 text-sm mt-1">AI-powered job evaluation &amp; routing</p>
        </div>
        <button
          onClick={handleBatchEvaluate}
          disabled={evaluating}
          className="btn-primary flex items-center gap-2"
        >
          {evaluating ? (
            <>
              <svg className="w-4 h-4 animate-spin" viewBox="0 0 24 24" fill="none">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
              </svg>
              Evaluating...
            </>
          ) : (
            <>
              <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
              </svg>
              Batch Evaluate
            </>
          )}
        </button>
      </div>

      {/* Stats */}
      {stats && (
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
          <StatCard label="Total Decisions" value={stats.total_decisions} accent="gold"
            icon={<span className="text-lg">🧠</span>} />
          <StatCard label="Executed" value={stats.executed} accent="green"
            icon={<span className="text-lg">✅</span>} />
          {Object.entries(stats.by_decision ?? {}).slice(0, 2).map(([d, c]) => {
            const cfg = decisionConfig[d];
            return (
              <StatCard key={d} label={d.replace(/_/g, ' ')} value={c}
                accent={cfg?.variant === 'green' ? 'green' : cfg?.variant === 'gold' ? 'gold' : 'cyan'}
                icon={<span className="text-lg">{cfg?.icon ?? '📋'}</span>} />
            );
          })}
        </div>
      )}

      {/* Filter Pills */}
      <div className="flex gap-2 flex-wrap">
        <button
          onClick={() => setFilter(null)}
          className={`px-3 py-1.5 rounded-full text-xs font-medium transition-all ${
            !filter ? 'bg-cyan-500/20 text-cyan-400 border border-cyan-500/30' : 'bg-navy-800 text-gray-400 border border-navy-700 hover:border-gray-600'
          }`}
        >
          All ({decisions.length})
        </button>
        {Object.entries(decisionConfig).map(([key, cfg]) => {
          const count = decisions.filter(d => d.decision === key).length;
          if (count === 0) return null;
          return (
            <button
              key={key}
              onClick={() => setFilter(filter === key ? null : key)}
              className={`px-3 py-1.5 rounded-full text-xs font-medium transition-all flex items-center gap-1.5 ${
                filter === key ? 'bg-cyan-500/20 text-cyan-400 border border-cyan-500/30' : 'bg-navy-800 text-gray-400 border border-navy-700 hover:border-gray-600'
              }`}
            >
              <span>{cfg.icon}</span>
              {key.replace(/_/g, ' ')} ({count})
            </button>
          );
        })}
      </div>

      {/* Decision List */}
      {filtered.length === 0 ? (
        <EmptyState
          icon="🧠"
          title="No Decisions Yet"
          description='Use "Batch Evaluate" to let AI score and route your discovered jobs.'
        />
      ) : (
        <div className="space-y-3">
          {filtered.map((d) => {
            const cfg = decisionConfig[d.decision] ?? { variant: 'gray' as const, icon: '📋' };
            const score = d.score_data?.score;
            return (
              <div key={d.id} className="card-hover p-4 flex items-center gap-4">
                {/* Score circle */}
                <div className="flex-shrink-0">
                  {score != null ? (
                    <div className={`w-12 h-12 rounded-full flex items-center justify-center text-lg font-bold ${
                      score >= 80 ? 'bg-cyan-500/20 text-cyan-400' :
                      score >= 60 ? 'bg-green-500/20 text-green-400' :
                      score >= 40 ? 'bg-gold-400/20 text-gold-400' :
                      'bg-red-500/20 text-red-400'
                    }`}>
                      {score}
                    </div>
                  ) : (
                    <div className="w-12 h-12 rounded-full bg-navy-800 flex items-center justify-center text-lg">
                      {cfg.icon}
                    </div>
                  )}
                </div>

                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 flex-wrap">
                    <Badge variant={cfg.variant} dot>{d.decision.replace(/_/g, ' ')}</Badge>
                    <span className="text-sm text-gray-300">{d.decision_type}</span>
                    {d.executed && (
                      <span className="text-xs text-green-400 flex items-center gap-1">
                        <svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                        </svg>
                        executed
                      </span>
                    )}
                  </div>
                  {d.reason && (
                    <p className="text-gray-400 text-sm mt-1 line-clamp-2">{d.reason}</p>
                  )}
                  {/* Score Breakdown */}
                  {d.score_data?.breakdown && (
                    <div className="flex gap-3 mt-2">
                      {Object.entries(d.score_data.breakdown).slice(0, 4).map(([k, v]) => (
                        <span key={k} className="text-[11px] text-gray-500">
                          <span className="text-gray-400">{k}:</span> {v}
                        </span>
                      ))}
                    </div>
                  )}
                </div>

                <div className="text-right flex-shrink-0">
                  <p className="text-xs text-gray-500">
                    {d.created_at ? new Date(d.created_at).toLocaleDateString() : ''}
                  </p>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
