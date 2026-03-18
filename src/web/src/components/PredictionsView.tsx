'use client';

import { useEffect, useState } from 'react';
import { predictionsApi } from '@/lib/api';
import { Badge, LoadingSpinner, StatCard, EmptyState } from '@/components/ui';

interface Trend {
  role: string;
  demand_change: number;
  avg_salary: number;
  top_skills: string[];
  recent_postings?: number;
  last_7d?: number;
  tech_stack?: Record<string, number>;
  avg_match_score?: number;
}

interface Opportunity {
  job_id: string;
  title: string;
  company: string;
  score: number;
  reasons: string[];
}

interface Stats {
  total_predictions: number;
  avg_confidence: number;
  top_sectors: string[];
}

export default function PredictionsView() {
  const [trends, setTrends] = useState<Trend[]>([]);
  const [opportunities, setOpportunities] = useState<Opportunity[]>([]);
  const [stats, setStats] = useState<Stats | null>(null);
  const [companyName, setCompanyName] = useState('');
  const [companyData, setCompanyData] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [tab, setTab] = useState<'trends' | 'opportunities' | 'company'>('trends');

  useEffect(() => {
    Promise.all([
      predictionsApi.getTrends().then(r => { const d = r.data?.trends ?? r.data; setTrends(Array.isArray(d) ? d : []); }).catch(() => {}),
      predictionsApi.getOpportunities().then(r => { const d = r.data?.opportunities ?? r.data; setOpportunities(Array.isArray(d) ? d : []); }).catch(() => {}),
      predictionsApi.getStats().then(r => setStats(r.data)).catch(() => {}),
    ]).finally(() => setLoading(false));
  }, []);

  const searchCompany = () => {
    if (!companyName.trim()) return;
    predictionsApi.getCompany(companyName)
      .then(r => setCompanyData(r.data))
      .catch(() => setCompanyData({ error: 'Company not found' }));
  };

  if (loading) return <LoadingSpinner text="Analyzing market predictions..." />;

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="page-title">Predictive AI</h1>
          <p className="text-gray-400 text-sm mt-1">Market trends, hiring predictions & opportunity ranking</p>
        </div>
        <Badge variant="purple" dot>AI Powered</Badge>
      </div>

      {/* Stats */}
      {stats && (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <StatCard label="Total Predictions" value={stats.total_predictions} icon="🔮" />
          <StatCard label="Avg Confidence" value={`${Math.round((stats.avg_confidence ?? 0) * 100)}%`} icon="🎯" />
          <StatCard label="Sectors Tracked" value={stats.top_sectors?.length ?? 0} icon="📊" />
        </div>
      )}

      {/* Tabs */}
      <div className="flex gap-2 border-b border-gray-700/30 pb-2">
        {(['trends', 'opportunities', 'company'] as const).map(t => (
          <button
            key={t}
            onClick={() => setTab(t)}
            className={`px-4 py-2 rounded-t-lg text-sm font-medium transition-all capitalize ${
              tab === t ? 'bg-cyan-400/10 text-cyan-400 border-b-2 border-cyan-400' : 'text-gray-400 hover:text-gray-200'
            }`}
          >
            {t === 'company' ? 'Company Lookup' : t}
          </button>
        ))}
      </div>

      {/* Trends Tab */}
      {tab === 'trends' && (
        <div className="space-y-3">
          {trends.length === 0 ? (
            <EmptyState title="No trends yet" description="Predictions will appear as data is collected" />
          ) : (
            trends.map((trend, i) => (
              <div key={i} className="card p-4 flex items-center justify-between">
                <div className="flex-1">
                  <h3 className="text-white font-medium">{trend.role}</h3>
                  <div className="flex gap-2 mt-2 flex-wrap">
                    {trend.top_skills?.map((s, j) => (
                      <span key={j} className="text-xs px-2 py-0.5 rounded-full bg-purple-400/10 text-purple-400">{s}</span>
                    ))}
                  </div>
                  {(trend.recent_postings != null || trend.avg_match_score != null) && (
                    <div className="flex gap-3 mt-2 text-xs text-gray-500">
                      {trend.recent_postings != null && <span>📊 {trend.recent_postings} postings (30d)</span>}
                      {trend.last_7d != null && <span>🔥 {trend.last_7d} this week</span>}
                      {trend.avg_match_score != null && <span>🎯 {Math.round(trend.avg_match_score)}% avg match</span>}
                    </div>
                  )}
                  {trend.tech_stack && Object.keys(trend.tech_stack).length > 0 && (
                    <div className="flex gap-1 mt-2 flex-wrap">
                      {Object.entries(trend.tech_stack).slice(0, 5).map(([tech, count]) => (
                        <span key={tech} className="text-[10px] px-1.5 py-0.5 rounded bg-cyan-400/10 text-cyan-400">{tech} ({count})</span>
                      ))}
                    </div>
                  )}
                </div>
                <div className="text-right">
                  <div className={`text-lg font-bold ${trend.demand_change >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                    {trend.demand_change >= 0 ? '+' : ''}{trend.demand_change}%
                  </div>
                  {trend.avg_salary > 0 && (
                    <div className="text-xs text-gray-500">${(trend.avg_salary / 1000).toFixed(0)}k avg</div>
                  )}
                </div>
              </div>
            ))
          )}
        </div>
      )}

      {/* Opportunities Tab */}
      {tab === 'opportunities' && (
        <div className="space-y-3">
          {opportunities.length === 0 ? (
            <EmptyState title="No opportunities ranked" description="Opportunity scoring runs automatically on new jobs" />
          ) : (
            opportunities.map((opp, i) => (
              <div key={i} className="card p-4">
                <div className="flex items-center justify-between">
                  <div>
                    <h3 className="text-white font-medium">{opp.title}</h3>
                    <p className="text-gray-400 text-sm">{opp.company}</p>
                  </div>
                  <div className="flex items-center gap-2">
                    <div className="text-right">
                      <div className="text-lg font-bold text-cyan-400">{Math.round(opp.score * 100)}%</div>
                      <div className="text-xs text-gray-500">match</div>
                    </div>
                  </div>
                </div>
                {opp.reasons?.length > 0 && (
                  <div className="mt-3 flex gap-2 flex-wrap">
                    {opp.reasons.map((r, j) => (
                      <Badge key={j} variant="green">{r}</Badge>
                    ))}
                  </div>
                )}
              </div>
            ))
          )}
        </div>
      )}

      {/* Company Lookup Tab */}
      {tab === 'company' && (
        <div className="space-y-4">
          <div className="card p-4 flex gap-3">
            <input
              type="text"
              value={companyName}
              onChange={e => setCompanyName(e.target.value)}
              onKeyDown={e => e.key === 'Enter' && searchCompany()}
              placeholder="Enter company name..."
              className="input-field flex-1"
            />
            <button onClick={searchCompany} className="btn-primary px-6">Analyze</button>
          </div>
          {companyData && !companyData.error && (
            <div className="card p-6 space-y-4">
              <h3 className="text-white text-lg font-semibold">{companyData.company_name}</h3>
              <div className="grid grid-cols-2 gap-4">
                <div className="bg-navy-800/50 rounded-xl p-4">
                  <div className="text-xs text-gray-500 mb-1">Hiring Velocity</div>
                  <div className="text-xl font-bold text-cyan-400">{companyData.hiring_velocity ?? 'N/A'}</div>
                </div>
                <div className="bg-navy-800/50 rounded-xl p-4">
                  <div className="text-xs text-gray-500 mb-1">Hire Probability</div>
                  <div className="text-xl font-bold text-green-400">{Math.round((companyData.hire_probability ?? 0) * 100)}%</div>
                </div>
              </div>
              {companyData.recent_signals?.length > 0 && (
                <div>
                  <div className="text-xs text-gray-500 mb-2">Recent Signals</div>
                  <div className="space-y-2">
                    {companyData.recent_signals.map((sig: any, k: number) => (
                      <div key={k} className="flex items-center gap-2 text-sm text-gray-300">
                        <span className="w-1.5 h-1.5 rounded-full bg-cyan-400" />
                        {sig.title ?? sig}
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}
          {companyData?.error && (
            <div className="card p-4 text-center text-gray-400">{companyData.error}</div>
          )}
        </div>
      )}
    </div>
  );
}
