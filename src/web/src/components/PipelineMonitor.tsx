'use client';

import { useEffect, useState } from 'react';
import { pipelineApi, crawlApi } from '@/lib/api';
import { StatCard, Badge, ProgressBar, LoadingSpinner } from '@/components/ui';

interface PipelineStats {
  total_events: number;
  events_by_type: Record<string, number>;
  total_jobs: number;
  total_signals: number;
}

interface CrawlStats {
  total_sources: number;
  active_crawlers: number;
  total_crawls_today: number;
  queue_size: number;
}

export default function PipelineMonitor() {
  const [pipelineStats, setPipelineStats] = useState<PipelineStats | null>(null);
  const [crawlStats, setCrawlStats] = useState<CrawlStats | null>(null);
  const [sources, setSources] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [triggering, setTriggering] = useState<string | null>(null);

  useEffect(() => {
    Promise.all([
      pipelineApi.getStats().catch(() => ({ data: {} })),
      crawlApi.getStats().catch(() => ({ data: {} })),
      crawlApi.getSources().catch(() => ({ data: [] })),
    ]).then(([pRes, cRes, sRes]) => {
      setPipelineStats(pRes.data);
      setCrawlStats(cRes.data);
      setSources(Array.isArray(sRes.data) ? sRes.data : []);
      setLoading(false);
    });
  }, []);

  const [triggerResult, setTriggerResult] = useState<{ name: string; ok: boolean } | null>(null);

  const handleTrigger = async (sourceName: string) => {
    setTriggering(sourceName);
    setTriggerResult(null);
    try {
      await crawlApi.triggerCrawl(sourceName);
      setTriggerResult({ name: sourceName, ok: true });
      // Refresh sources after trigger
      const sRes = await crawlApi.getSources().catch(() => ({ data: [] }));
      setSources(Array.isArray(sRes.data) ? sRes.data : []);
      const cRes = await crawlApi.getStats().catch(() => ({ data: {} }));
      setCrawlStats(cRes.data);
    } catch {
      setTriggerResult({ name: sourceName, ok: false });
    } finally {
      setTriggering(null);
      setTimeout(() => setTriggerResult(null), 4000);
    }
  };

  if (loading) return <LoadingSpinner text="Loading pipeline data..." />;

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="page-title">Pipeline Monitor</h1>
          <p className="text-gray-400 text-sm mt-1">Data ingestion &amp; crawler management</p>
        </div>
        <Badge variant="green" dot>Operational</Badge>
      </div>

      {/* Top Stats */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard label="Total Events" value={pipelineStats?.total_events ?? 0} accent="cyan"
          icon={<svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M13 10V3L4 14h7v7l9-11h-7z" /></svg>}
        />
        <StatCard label="Jobs Ingested" value={pipelineStats?.total_jobs ?? 0} accent="green"
          icon={<svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M20 13V6a2 2 0 00-2-2H6a2 2 0 00-2 2v7m16 0v5a2 2 0 01-2 2H6a2 2 0 01-2-2v-5m16 0h-2.586a1 1 0 00-.707.293l-2.414 2.414a1 1 0 01-.707.293h-3.172a1 1 0 01-.707-.293l-2.414-2.414A1 1 0 006.586 13H4" /></svg>}
        />
        <StatCard label="Signals Detected" value={pipelineStats?.total_signals ?? 0} accent="gold"
          icon={<svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" /></svg>}
        />
        <StatCard label="Crawler Sources" value={crawlStats?.total_sources ?? sources.length} accent="purple"
          icon={<svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M21 12a9 9 0 01-9 9m9-9a9 9 0 00-9-9m9 9H3m9 9a9 9 0 01-9-9m9 9c1.657 0 3-4.03 3-9s-1.343-9-3-9m0 18c-1.657 0-3-4.03-3-9s1.343-9 3-9m-9 9a9 9 0 019-9" /></svg>}
        />
      </div>

      {/* Events by Type */}
      {pipelineStats?.events_by_type && Object.keys(pipelineStats.events_by_type).length > 0 && (
        <div className="card p-6">
          <h2 className="section-title mb-4">Events by Type</h2>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
            {Object.entries(pipelineStats.events_by_type).map(([type, count]) => (
              <div key={type} className="bg-navy-950 rounded-xl p-4 text-center hover:bg-navy-950/80 transition-colors">
                <p className="text-xl font-bold text-white">{count}</p>
                <p className="text-[10px] text-gray-500 uppercase tracking-wider mt-1 capitalize">{type.replace(/_/g, ' ')}</p>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Trigger feedback */}
      {triggerResult && (
        <div className={`rounded-xl px-4 py-3 text-sm font-medium ${
          triggerResult.ok
            ? 'bg-green-500/10 border border-green-500/30 text-green-400'
            : 'bg-red-500/10 border border-red-500/30 text-red-400'
        }`}>
          {triggerResult.ok
            ? `✓ Crawl queued for "${triggerResult.name}" — processing in background`
            : `✗ Failed to trigger crawl for "${triggerResult.name}"`}
        </div>
      )}

      {/* Crawler Sources */}
      <div className="card p-6">
        <div className="flex items-center justify-between mb-4">
          <h2 className="section-title">Crawler Sources</h2>
          <span className="text-xs text-gray-500">{sources.length} configured</span>
        </div>
        {sources.length === 0 ? (
          <p className="text-gray-500 text-sm text-center py-6">No crawler sources configured yet.</p>
        ) : (
          <div className="space-y-2">
            {sources.map((src: any, i: number) => (
              <div
                key={src.id ?? src.name}
                className="flex items-center justify-between bg-navy-950 rounded-xl px-4 py-3 hover:bg-navy-950/80 transition-colors animate-slide-up"
                style={{ animationDelay: `${i * 30}ms` }}
              >
                <div className="flex items-center gap-3">
                  <div className={`w-2 h-2 rounded-full ${src.is_enabled ? 'bg-green-400 animate-pulse' : 'bg-gray-600'}`} />
                  <div>
                    <span className="text-sm text-white font-medium">{src.name}</span>
                    <Badge variant="gray">{src.crawler_type}</Badge>
                  </div>
                </div>
                <div className="flex items-center gap-3">
                  <Badge variant={src.is_enabled ? 'green' : 'gray'} dot>{src.is_enabled ? 'Active' : 'Disabled'}</Badge>
                  <button
                    onClick={() => handleTrigger(src.name)}
                    disabled={triggering === src.name}
                    className="btn-primary text-xs py-1.5 disabled:opacity-50"
                  >
                    {triggering === src.name ? (
                      <svg className="w-3 h-3 animate-spin" fill="none" viewBox="0 0 24 24">
                        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                      </svg>
                    ) : 'Trigger'}
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
