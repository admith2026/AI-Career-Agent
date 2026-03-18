'use client';

import { useEffect, useState } from 'react';
import { graphApi } from '@/lib/api';
import { StatCard, Badge, ProgressBar, LoadingSpinner, EmptyState } from '@/components/ui';

interface Hotspot {
  company: string;
  signal_count: number;
  signal_types: string[];
  max_confidence: number;
}

interface TechDemand {
  technology: string;
  demand: number;
}

interface GraphStats {
  company_count: number;
  recruiter_count: number;
  jobrole_count: number;
  technology_count: number;
  hiringsignal_count: number;
  total_relationships: number;
}

export default function KnowledgeGraphView() {
  const [hotspots, setHotspots] = useState<Hotspot[]>([]);
  const [techDemand, setTechDemand] = useState<TechDemand[]>([]);
  const [stats, setStats] = useState<GraphStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [companySearch, setCompanySearch] = useState('');

  useEffect(() => {
    Promise.all([
      graphApi.getHotspots(15).catch(() => ({ data: [] })),
      graphApi.getTechDemand(15).catch(() => ({ data: [] })),
      graphApi.getStats().catch(() => ({ data: {} })),
    ]).then(([hRes, tRes, sRes]) => {
      setHotspots(Array.isArray(hRes.data) ? hRes.data : []);
      setTechDemand(Array.isArray(tRes.data) ? tRes.data : []);
      setStats(sRes.data);
      setLoading(false);
    });
  }, []);

  if (loading) return <LoadingSpinner text="Loading knowledge graph..." />;

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="page-title">Knowledge Graph</h1>
          <p className="text-gray-400 text-sm mt-1">Company intelligence &amp; technology landscape</p>
        </div>
        <Badge variant="purple" dot>Neo4j Connected</Badge>
      </div>

      {/* Graph Stats */}
      {stats && (
        <div className="grid grid-cols-2 lg:grid-cols-3 gap-4">
          <StatCard label="Companies" value={stats.company_count ?? 0} accent="cyan"
            icon={<span className="text-lg">🏢</span>} />
          <StatCard label="Recruiters" value={stats.recruiter_count ?? 0} accent="purple"
            icon={<span className="text-lg">👤</span>} />
          <StatCard label="Job Roles" value={stats.jobrole_count ?? 0} accent="gold"
            icon={<span className="text-lg">💼</span>} />
          <StatCard label="Technologies" value={stats.technology_count ?? 0} accent="green"
            icon={<span className="text-lg">⚡</span>} />
          <StatCard label="Hiring Signals" value={stats.hiringsignal_count ?? 0} accent="red"
            icon={<span className="text-lg">📡</span>} />
          <StatCard label="Relationships" value={stats.total_relationships ?? 0} accent="cyan"
            icon={<span className="text-lg">🔗</span>} />
        </div>
      )}

      {/* Company Search */}
      <div className="card p-4">
        <div className="relative">
          <svg className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
          </svg>
          <input
            type="text"
            value={companySearch}
            onChange={(e) => setCompanySearch(e.target.value)}
            placeholder="Search companies in the graph..."
            className="input-field pl-10"
          />
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Hiring Hotspots */}
        <div className="card p-6">
          <div className="flex items-center gap-2 mb-4">
            <span className="text-lg">🔥</span>
            <h2 className="section-title">Hiring Hotspots</h2>
          </div>
          {hotspots.length === 0 ? (
            <p className="text-gray-500 text-sm text-center py-6">No data yet.</p>
          ) : (
            <div className="space-y-3">
              {hotspots.filter(h => !companySearch || h.company.toLowerCase().includes(companySearch.toLowerCase())).map((h, i) => (
                <div key={i} className="flex items-center gap-3 p-2.5 rounded-xl hover:bg-navy-950/50 transition-colors">
                  <div className="text-right w-6">
                    <span className="text-xs text-gray-500 font-mono">#{i + 1}</span>
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2">
                      <span className="text-sm text-white font-medium truncate">{h.company}</span>
                    </div>
                    <div className="flex gap-1 mt-1">
                      {(h.signal_types ?? []).slice(0, 3).map((t, j) => (
                        <Badge key={j} variant="purple">{t.replace(/_/g, ' ')}</Badge>
                      ))}
                    </div>
                  </div>
                  <div className="text-right flex-shrink-0">
                    <span className="text-lg font-bold text-white">{h.signal_count}</span>
                    <p className="text-[10px] text-gray-500">signals</p>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Technology Demand */}
        <div className="card p-6">
          <div className="flex items-center gap-2 mb-4">
            <span className="text-lg">📈</span>
            <h2 className="section-title">Technology Demand</h2>
          </div>
          {techDemand.length === 0 ? (
            <p className="text-gray-500 text-sm text-center py-6">No data yet.</p>
          ) : (
            <div className="space-y-3">
              {techDemand.map((t, i) => {
                const maxDemand = techDemand[0]?.demand ?? 1;
                const pct = (t.demand / maxDemand) * 100;
                return (
                  <div key={i} className="flex items-center gap-3">
                    <span className="text-xs text-gray-500 font-mono w-6 text-right">#{i + 1}</span>
                    <span className="text-sm text-gray-300 w-28 truncate">{t.technology}</span>
                    <div className="flex-1">
                      <div className="h-2 bg-navy-950 rounded-full overflow-hidden">
                        <div
                          className="h-full rounded-full bg-gradient-to-r from-purple-500 to-pink-500 transition-all duration-700"
                          style={{ width: `${pct}%` }}
                        />
                      </div>
                    </div>
                    <span className="text-sm text-white font-medium w-10 text-right">{t.demand}</span>
                  </div>
                );
              })}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
