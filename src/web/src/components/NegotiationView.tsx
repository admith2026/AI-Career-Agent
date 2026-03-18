'use client';

import { useEffect, useState } from 'react';
import { negotiationApi } from '@/lib/api';
import { Badge, LoadingSpinner, StatCard, EmptyState } from '@/components/ui';

interface Strategy {
  id: string;
  job_title: string;
  company_name: string;
  current_offer: number;
  desired_salary: number;
  counter_offer: number;
  confidence_score: number;
  negotiation_points: string[];
  counter_script: string;
  status: string;
  created_at: string;
}

interface Stats {
  total_strategies: number;
  avg_increase: number;
  success_rate: number;
  total_value_gained: number;
}

export default function NegotiationView() {
  const [strategies, setStrategies] = useState<Strategy[]>([]);
  const [stats, setStats] = useState<Stats | null>(null);
  const [loading, setLoading] = useState(true);
  const [showAnalyzeForm, setShowAnalyzeForm] = useState(false);
  const [analyzeForm, setAnalyzeForm] = useState({ job_title: '', company_name: '', current_offer: '', desired_salary: '', years_experience: '', location: '' });
  const [selectedStrategy, setSelectedStrategy] = useState<string | null>(null);
  const [marketRole, setMarketRole] = useState('');
  const [marketRates, setMarketRates] = useState<any>(null);

  const load = () => {
    Promise.all([
      negotiationApi.getStrategies().then(r => { const d = r.data?.strategies ?? r.data; setStrategies(Array.isArray(d) ? d : []); }).catch(() => {}),
      negotiationApi.getStats().then(r => setStats(r.data)).catch(() => {}),
    ]).finally(() => setLoading(false));
  };

  useEffect(() => { load(); }, []);

  const analyzeOffer = () => {
    if (!analyzeForm.job_title.trim() || !analyzeForm.current_offer) return;
    negotiationApi.analyze({
      ...analyzeForm,
      current_offer: parseFloat(analyzeForm.current_offer),
      desired_salary: parseFloat(analyzeForm.desired_salary) || undefined,
      years_experience: parseInt(analyzeForm.years_experience) || undefined,
    })
      .then(() => { setShowAnalyzeForm(false); setAnalyzeForm({ job_title: '', company_name: '', current_offer: '', desired_salary: '', years_experience: '', location: '' }); load(); })
      .catch(() => {});
  };

  const searchMarketRates = () => {
    if (!marketRole.trim()) return;
    negotiationApi.getMarketRates(marketRole)
      .then(r => setMarketRates(r.data))
      .catch(() => setMarketRates(null));
  };

  const updateStatus = (id: string, status: string) => {
    negotiationApi.updateStatus(id, status).then(() => load()).catch(() => {});
  };

  if (loading) return <LoadingSpinner text="Loading negotiation strategies..." />;

  const statusColors: Record<string, 'gold' | 'cyan' | 'green' | 'red' | 'purple'> = {
    draft: 'gold', active: 'cyan', accepted: 'green', rejected: 'red', countered: 'purple'
  };

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="page-title">Negotiation AI</h1>
          <p className="text-gray-400 text-sm mt-1">Offer analysis, market rates & counter-offer strategies</p>
        </div>
        <button onClick={() => setShowAnalyzeForm(!showAnalyzeForm)} className="btn-primary">
          + Analyze Offer
        </button>
      </div>

      {/* Stats */}
      {stats && (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <StatCard label="Strategies" value={stats.total_strategies} icon="🎯" />
          <StatCard label="Avg Increase" value={`${Math.round(stats.avg_increase ?? 0)}%`} icon="📈" />
          <StatCard label="Success Rate" value={`${Math.round((stats.success_rate ?? 0) * 100)}%`} icon="✅" />
          <StatCard label="Value Gained" value={`$${((stats.total_value_gained ?? 0) / 1000).toFixed(0)}k`} icon="💰" />
        </div>
      )}

      {/* Analyze Form */}
      {showAnalyzeForm && (
        <div className="card p-6 space-y-4">
          <h3 className="text-white font-medium">Analyze an Offer</h3>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <input type="text" value={analyzeForm.job_title} onChange={e => setAnalyzeForm({...analyzeForm, job_title: e.target.value})} placeholder="Job title" className="input-field" />
            <input type="text" value={analyzeForm.company_name} onChange={e => setAnalyzeForm({...analyzeForm, company_name: e.target.value})} placeholder="Company" className="input-field" />
            <input type="number" value={analyzeForm.current_offer} onChange={e => setAnalyzeForm({...analyzeForm, current_offer: e.target.value})} placeholder="Current offer ($)" className="input-field" />
            <input type="number" value={analyzeForm.desired_salary} onChange={e => setAnalyzeForm({...analyzeForm, desired_salary: e.target.value})} placeholder="Desired salary ($)" className="input-field" />
            <input type="number" value={analyzeForm.years_experience} onChange={e => setAnalyzeForm({...analyzeForm, years_experience: e.target.value})} placeholder="Years experience" className="input-field" />
            <input type="text" value={analyzeForm.location} onChange={e => setAnalyzeForm({...analyzeForm, location: e.target.value})} placeholder="Location" className="input-field" />
          </div>
          <div className="flex gap-3">
            <button onClick={analyzeOffer} className="btn-primary">Analyze</button>
            <button onClick={() => setShowAnalyzeForm(false)} className="px-4 py-2 text-sm text-gray-400 hover:text-gray-200 transition-colors">Cancel</button>
          </div>
        </div>
      )}

      {/* Market Rate Lookup */}
      <div className="card p-4">
        <div className="flex gap-3">
          <input type="text" value={marketRole} onChange={e => setMarketRole(e.target.value)} onKeyDown={e => e.key === 'Enter' && searchMarketRates()} placeholder="Look up market rates by role..." className="input-field flex-1" />
          <button onClick={searchMarketRates} className="btn-primary px-6">Lookup</button>
        </div>
        {marketRates && (
          <div className="mt-4 grid grid-cols-3 gap-4">
            <div className="bg-navy-800/50 rounded-xl p-4 text-center">
              <div className="text-xs text-gray-500 mb-1">Low</div>
              <div className="text-lg font-bold text-red-400">${((marketRates.low ?? 0) / 1000).toFixed(0)}k</div>
            </div>
            <div className="bg-navy-800/50 rounded-xl p-4 text-center">
              <div className="text-xs text-gray-500 mb-1">Median</div>
              <div className="text-lg font-bold text-cyan-400">${((marketRates.median ?? 0) / 1000).toFixed(0)}k</div>
            </div>
            <div className="bg-navy-800/50 rounded-xl p-4 text-center">
              <div className="text-xs text-gray-500 mb-1">High</div>
              <div className="text-lg font-bold text-green-400">${((marketRates.high ?? 0) / 1000).toFixed(0)}k</div>
            </div>
          </div>
        )}
      </div>

      {/* Strategies List */}
      <div className="space-y-3">
        {strategies.length === 0 ? (
          <EmptyState title="No strategies yet" description="Analyze your first offer to get AI-powered negotiation strategies" />
        ) : (
          strategies.map(strat => (
            <div key={strat.id} className="card p-4 cursor-pointer hover:border-cyan-400/30 transition-all" onClick={() => setSelectedStrategy(selectedStrategy === strat.id ? null : strat.id)}>
              <div className="flex items-center justify-between">
                <div>
                  <div className="flex items-center gap-2">
                    <h3 className="text-white font-medium">{strat.job_title}</h3>
                    <Badge variant={statusColors[strat.status] ?? 'gold'}>{strat.status}</Badge>
                  </div>
                  <p className="text-gray-400 text-sm mt-0.5">{strat.company_name}</p>
                </div>
                <div className="text-right">
                  <div className="text-lg font-bold text-cyan-400">${(strat.counter_offer / 1000).toFixed(0)}k</div>
                  <div className="text-xs text-gray-500">vs ${(strat.current_offer / 1000).toFixed(0)}k offer</div>
                </div>
              </div>
              {selectedStrategy === strat.id && (
                <div className="mt-4 space-y-4">
                  <div className="grid grid-cols-3 gap-4">
                    <div className="bg-navy-800/50 rounded-xl p-3 text-center">
                      <div className="text-xs text-gray-500">Current</div>
                      <div className="text-sm font-bold text-gold-400">${(strat.current_offer / 1000).toFixed(0)}k</div>
                    </div>
                    <div className="bg-navy-800/50 rounded-xl p-3 text-center">
                      <div className="text-xs text-gray-500">Counter</div>
                      <div className="text-sm font-bold text-cyan-400">${(strat.counter_offer / 1000).toFixed(0)}k</div>
                    </div>
                    <div className="bg-navy-800/50 rounded-xl p-3 text-center">
                      <div className="text-xs text-gray-500">Confidence</div>
                      <div className="text-sm font-bold text-green-400">{Math.round(strat.confidence_score * 100)}%</div>
                    </div>
                  </div>
                  {strat.negotiation_points?.length > 0 && (
                    <div>
                      <h4 className="text-xs text-gray-500 uppercase tracking-wide mb-2">Negotiation Points</h4>
                      <div className="space-y-1">
                        {strat.negotiation_points.map((p, i) => (
                          <div key={i} className="flex items-start gap-2 text-sm text-gray-300">
                            <span className="text-cyan-400 mt-0.5">→</span> {p}
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                  {strat.counter_script && (
                    <div>
                      <h4 className="text-xs text-gray-500 uppercase tracking-wide mb-2">Counter Script</h4>
                      <p className="text-sm text-gray-300 bg-navy-800/50 rounded-lg p-3 italic">&ldquo;{strat.counter_script}&rdquo;</p>
                    </div>
                  )}
                  <div className="flex gap-2">
                    {strat.status === 'draft' && <button onClick={(e) => { e.stopPropagation(); updateStatus(strat.id, 'active'); }} className="text-xs px-3 py-1.5 rounded-lg bg-cyan-400/10 text-cyan-400 hover:bg-cyan-400/20 transition-all">Activate</button>}
                    {strat.status === 'active' && (
                      <>
                        <button onClick={(e) => { e.stopPropagation(); updateStatus(strat.id, 'accepted'); }} className="text-xs px-3 py-1.5 rounded-lg bg-green-400/10 text-green-400 hover:bg-green-400/20 transition-all">Accepted</button>
                        <button onClick={(e) => { e.stopPropagation(); updateStatus(strat.id, 'rejected'); }} className="text-xs px-3 py-1.5 rounded-lg bg-red-400/10 text-red-400 hover:bg-red-400/20 transition-all">Rejected</button>
                      </>
                    )}
                  </div>
                </div>
              )}
            </div>
          ))
        )}
      </div>
    </div>
  );
}
