'use client';

import { useEffect, useState } from 'react';
import { pipelineApi } from '@/lib/api';
import { Badge, LoadingSpinner, EmptyState } from '@/components/ui';

interface Signal {
  id: string;
  company_name: string;
  signal_type: string;
  title: string;
  confidence: number;
  source_url: string;
  detected_at: string;
}

const signalConfig: Record<string, { variant: 'green' | 'cyan' | 'purple' | 'gold' | 'red' | 'orange' | 'blue'; icon: string }> = {
  funding_round: { variant: 'green', icon: '💰' },
  team_expansion: { variant: 'cyan', icon: '📈' },
  product_launch: { variant: 'purple', icon: '🚀' },
  acquisition: { variant: 'gold', icon: '🤝' },
  exec_hire: { variant: 'red', icon: '👔' },
  expansion: { variant: 'blue', icon: '🌍' },
  ipo_filing: { variant: 'orange', icon: '📊' },
};

export default function HiringSignals() {
  const [signals, setSignals] = useState<Signal[]>([]);
  const [loading, setLoading] = useState(true);
  const [typeFilter, setTypeFilter] = useState('');

  useEffect(() => {
    pipelineApi.getSignals(100)
      .then((res) => setSignals(res.data.items ?? res.data ?? []))
      .catch(() => setSignals([]))
      .finally(() => setLoading(false));
  }, []);

  const signalTypes = Array.from(new Set(signals.map((s) => s.signal_type)));
  const filtered = typeFilter ? signals.filter((s) => s.signal_type === typeFilter) : signals;

  if (loading) return <LoadingSpinner text="Detecting hiring signals..." />;

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="page-title">Hiring Signals</h1>
          <p className="text-gray-400 text-sm mt-1">{signals.length} signals detected across companies</p>
        </div>
        <Badge variant="cyan" dot>Real-time</Badge>
      </div>

      {/* Type filters */}
      {signalTypes.length > 0 && (
        <div className="flex gap-2 flex-wrap">
          <button
            onClick={() => setTypeFilter('')}
            className={`px-3 py-1.5 rounded-xl text-xs font-medium transition-all ${
              typeFilter === '' ? 'bg-cyan-400/10 text-cyan-400 border border-cyan-400/30' : 'bg-surface text-gray-400 border border-transparent'
            }`}
          >
            All ({signals.length})
          </button>
          {signalTypes.map((t) => {
            const cfg = signalConfig[t] || { variant: 'gray' as const, icon: '📡' };
            return (
              <button
                key={t}
                onClick={() => setTypeFilter(typeFilter === t ? '' : t)}
                className={`px-3 py-1.5 rounded-xl text-xs font-medium transition-all capitalize ${
                  typeFilter === t ? 'bg-cyan-400/10 text-cyan-400 border border-cyan-400/30' : 'bg-surface text-gray-400 border border-transparent'
                }`}
              >
                {cfg.icon} {t.replace(/_/g, ' ')} ({signals.filter((s) => s.signal_type === t).length})
              </button>
            );
          })}
        </div>
      )}

      {filtered.length === 0 ? (
        <EmptyState
          icon="📡"
          title="No hiring signals detected yet"
          description="The crawl engine will discover them automatically as it monitors companies."
        />
      ) : (
        <div className="space-y-2">
          {filtered.map((s, i) => {
            const cfg = signalConfig[s.signal_type] || { variant: 'gray' as const, icon: '📡' };
            return (
              <div
                key={s.id}
                className="card-hover p-4 flex items-center gap-4 animate-slide-up"
                style={{ animationDelay: `${i * 20}ms` }}
              >
                <div className="w-10 h-10 rounded-xl bg-surface-light flex items-center justify-center text-lg flex-shrink-0">
                  {cfg.icon}
                </div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 mb-0.5">
                    <span className="text-sm font-semibold text-white">{s.company_name}</span>
                    <Badge variant={cfg.variant}>{s.signal_type.replace(/_/g, ' ')}</Badge>
                  </div>
                  <p className="text-sm text-gray-400 truncate">{s.title}</p>
                </div>
                <div className="text-right flex-shrink-0">
                  <div className="flex items-center gap-1.5">
                    <div className="w-16 h-1.5 bg-navy-950 rounded-full overflow-hidden">
                      <div
                        className={`h-full rounded-full ${
                          s.confidence >= 0.8 ? 'bg-green-400' : s.confidence >= 0.5 ? 'bg-gold-400' : 'bg-gray-500'
                        }`}
                        style={{ width: `${s.confidence * 100}%` }}
                      />
                    </div>
                    <span className="text-xs text-gray-400 w-8">{Math.round(s.confidence * 100)}%</span>
                  </div>
                  <p className="text-[10px] text-gray-600 mt-1">
                    {s.detected_at ? new Date(s.detected_at).toLocaleDateString() : ''}
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
