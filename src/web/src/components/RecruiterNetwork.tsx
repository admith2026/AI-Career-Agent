'use client';

import { useEffect, useState } from 'react';
import { recruitersApi } from '@/lib/api';
import { Badge, LoadingSpinner, EmptyState } from '@/components/ui';

interface Recruiter {
  id: string;
  name: string;
  company: string;
  email: string | null;
  phone: string | null;
  specializations: string[];
  intelligence_score: number | null;
  response_rate: number | null;
  total_interactions: number;
  successful_placements: number;
}

export default function RecruiterNetwork() {
  const [recruiters, setRecruiters] = useState<Recruiter[]>([]);
  const [topRanked, setTopRanked] = useState<Recruiter[]>([]);
  const [stats, setStats] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [view, setView] = useState<'list' | 'grid'>('list');
  const [showAddForm, setShowAddForm] = useState(false);
  const [newRecruiter, setNewRecruiter] = useState({ name: '', company: '', email: '', phone: '' });

  const load = () => {
    setLoading(true);
    Promise.all([
      recruitersApi.list().then(r => setRecruiters(r.data ?? [])).catch(() => setRecruiters([])),
      recruitersApi.getTopRanked(10).then(r => setTopRanked(r.data ?? [])).catch(() => setTopRanked([])),
      recruitersApi.getStatsSummary().then(r => setStats(r.data)).catch(() => {}),
    ]).finally(() => setLoading(false));
  };

  useEffect(() => { load(); }, []);

  const handleAdd = async () => {
    if (!newRecruiter.name || !newRecruiter.company) return;
    await recruitersApi.create(newRecruiter);
    setNewRecruiter({ name: '', company: '', email: '', phone: '' });
    setShowAddForm(false);
    load();
  };

  const handleInteraction = async (id: string, type: string) => {
    await recruitersApi.recordInteraction(id, type);
    load();
  };

  const filtered = recruiters.filter(r =>
    !search || r.name.toLowerCase().includes(search.toLowerCase()) || r.company.toLowerCase().includes(search.toLowerCase())
  );

  if (loading) return <LoadingSpinner text="Loading recruiter network..." />;

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="page-title">Recruiter Network</h1>
          <p className="text-gray-400 text-sm mt-1">Manage your recruiter and vendor relationships</p>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={() => setView('list')}
            className={`p-2 rounded-lg transition-all ${view === 'list' ? 'bg-cyan-400/10 text-cyan-400' : 'text-gray-500 hover:text-gray-300'}`}
          >
            <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M4 6h16M4 12h16M4 18h16" />
            </svg>
          </button>
          <button
            onClick={() => setView('grid')}
            className={`p-2 rounded-lg transition-all ${view === 'grid' ? 'bg-cyan-400/10 text-cyan-400' : 'text-gray-500 hover:text-gray-300'}`}
          >
            <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M4 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2V6zM14 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2V6zM4 16a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2v-2zM14 16a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2v-2z" />
            </svg>
          </button>
        </div>
      </div>

      {/* Search + Add */}
      <div className="card p-4">
        <div className="flex items-center gap-3">
          <div className="relative flex-1">
            <svg className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
            </svg>
            <input
              type="text"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Search recruiters, companies..."
              className="input-field pl-10"
            />
          </div>
          <button onClick={() => setShowAddForm(!showAddForm)} className="btn-primary text-sm whitespace-nowrap">
            + Add Recruiter
          </button>
        </div>
      </div>

      {/* Add Recruiter Form */}
      {showAddForm && (
        <div className="card p-6 animate-slide-up">
          <h3 className="text-sm font-semibold text-white mb-4">Add New Recruiter</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <input type="text" value={newRecruiter.name} onChange={(e) => setNewRecruiter(r => ({ ...r, name: e.target.value }))} placeholder="Full Name *" className="input-field text-sm" />
            <input type="text" value={newRecruiter.company} onChange={(e) => setNewRecruiter(r => ({ ...r, company: e.target.value }))} placeholder="Company *" className="input-field text-sm" />
            <input type="email" value={newRecruiter.email} onChange={(e) => setNewRecruiter(r => ({ ...r, email: e.target.value }))} placeholder="Email" className="input-field text-sm" />
            <input type="tel" value={newRecruiter.phone} onChange={(e) => setNewRecruiter(r => ({ ...r, phone: e.target.value }))} placeholder="Phone" className="input-field text-sm" />
          </div>
          <div className="flex gap-2 mt-4">
            <button onClick={handleAdd} className="btn-primary text-sm">Save</button>
            <button onClick={() => setShowAddForm(false)} className="btn-secondary text-sm">Cancel</button>
          </div>
        </div>
      )}

      {/* Stats Overview */}
      {stats && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="card p-4 text-center">
            <p className="text-2xl font-bold text-white">{stats.total ?? 0}</p>
            <p className="text-xs text-gray-500 uppercase tracking-wider">Total Recruiters</p>
          </div>
          <div className="card p-4 text-center">
            <p className="text-2xl font-bold text-cyan-400">{stats.avg_intelligence_score?.toFixed(0) ?? '—'}</p>
            <p className="text-xs text-gray-500 uppercase tracking-wider">Avg Intelligence Score</p>
          </div>
          <div className="card p-4 text-center">
            <p className="text-2xl font-bold text-green-400">{stats.total_interactions ?? 0}</p>
            <p className="text-xs text-gray-500 uppercase tracking-wider">Total Interactions</p>
          </div>
          <div className="card p-4 text-center">
            <p className="text-2xl font-bold text-purple-400">{stats.total_placements ?? 0}</p>
            <p className="text-xs text-gray-500 uppercase tracking-wider">Placements</p>
          </div>
        </div>
      )}

      {/* Top Ranked */}
      {topRanked.length > 0 && (
        <div className="card p-6">
          <h2 className="section-title mb-4">🏆 Top Ranked Recruiters</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
            {topRanked.slice(0, 6).map((r, i) => (
              <div key={r.id} className="card-hover p-4 flex items-center gap-3">
                <div className={`w-8 h-8 rounded-lg flex items-center justify-center text-sm font-bold ${
                  i === 0 ? 'bg-gold-400/20 text-gold-400' : i === 1 ? 'bg-gray-300/20 text-gray-300' : i === 2 ? 'bg-amber-600/20 text-amber-500' : 'bg-navy-800 text-gray-400'
                }`}>#{i + 1}</div>
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium text-white truncate">{r.name}</p>
                  <p className="text-xs text-gray-500">{r.company}</p>
                </div>
                <div className="text-right">
                  <p className="text-sm font-bold text-cyan-400">{r.intelligence_score ?? 0}</p>
                  <p className="text-[10px] text-gray-500">score</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Recruiter List */}
      {filtered.length === 0 ? (
        <EmptyState
          icon="👤"
          title="No recruiters found"
          description="Add recruiters manually or let the system discover them through job analysis and crawling."
        />
      ) : view === 'list' ? (
        <div className="space-y-2">
          {filtered.map((r) => (
            <div key={r.id} className="card-hover p-4 flex items-center gap-4">
              <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-purple-500 to-pink-500 flex items-center justify-center text-white font-bold text-sm flex-shrink-0">
                {r.name.charAt(0)}
              </div>
              <div className="flex-1 min-w-0">
                <h3 className="text-sm font-medium text-white">{r.name}</h3>
                <p className="text-xs text-gray-500">{r.company}{r.email ? ` · ${r.email}` : ''}</p>
              </div>
              <div className="flex items-center gap-2">
                {r.specializations?.slice(0, 2).map((s: string) => (
                  <Badge key={s} variant="purple">{s}</Badge>
                ))}
                {r.intelligence_score != null && (
                  <div className={`px-2 py-1 rounded-lg text-xs font-bold ${
                    r.intelligence_score >= 70 ? 'bg-green-400/10 text-green-400' :
                    r.intelligence_score >= 40 ? 'bg-gold-400/10 text-gold-400' :
                    'bg-gray-700 text-gray-400'
                  }`}>{r.intelligence_score}pts</div>
                )}
                <span className="text-xs text-gray-500">{r.total_interactions} interactions</span>
              </div>
              <div className="flex gap-1">
                <button onClick={() => handleInteraction(r.id, 'email_sent')} className="text-xs px-2 py-1 rounded-lg bg-cyan-400/5 text-cyan-400 hover:bg-cyan-400/15 transition-all" title="Log email">📧</button>
                <button onClick={() => handleInteraction(r.id, 'call')} className="text-xs px-2 py-1 rounded-lg bg-green-400/5 text-green-400 hover:bg-green-400/15 transition-all" title="Log call">📞</button>
                <button onClick={() => handleInteraction(r.id, 'response_received')} className="text-xs px-2 py-1 rounded-lg bg-purple-400/5 text-purple-400 hover:bg-purple-400/15 transition-all" title="Log response">💬</button>
              </div>
            </div>
          ))}
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {filtered.map((r) => (
            <div key={r.id} className="card-hover p-6 text-center">
              <div className="w-14 h-14 rounded-xl bg-gradient-to-br from-purple-500 to-pink-500 flex items-center justify-center text-white font-bold text-xl mx-auto mb-3">
                {r.name.charAt(0)}
              </div>
              <h3 className="text-sm font-medium text-white">{r.name}</h3>
              <p className="text-xs text-gray-500 mb-2">{r.company}</p>
              {r.intelligence_score != null && (
                <p className="text-lg font-bold text-cyan-400 mb-2">{r.intelligence_score} <span className="text-xs text-gray-500 font-normal">pts</span></p>
              )}
              <div className="flex justify-center gap-1 flex-wrap mb-3">
                {r.specializations?.map((s: string) => (
                  <Badge key={s} variant="purple">{s}</Badge>
                ))}
              </div>
              <div className="flex justify-center gap-1">
                <button onClick={() => handleInteraction(r.id, 'email_sent')} className="text-xs px-2 py-1 rounded-lg bg-cyan-400/5 text-cyan-400 hover:bg-cyan-400/15">📧</button>
                <button onClick={() => handleInteraction(r.id, 'call')} className="text-xs px-2 py-1 rounded-lg bg-green-400/5 text-green-400 hover:bg-green-400/15">📞</button>
                <button onClick={() => handleInteraction(r.id, 'response_received')} className="text-xs px-2 py-1 rounded-lg bg-purple-400/5 text-purple-400 hover:bg-purple-400/15">💬</button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
