'use client';

import { useEffect, useState } from 'react';
import { freelanceApi } from '@/lib/api';
import { Badge, LoadingSpinner, StatCard, EmptyState } from '@/components/ui';

interface Bid {
  id: string;
  platform: string;
  project_title: string;
  project_url: string;
  bid_amount: number;
  estimated_hours: number;
  proposal_text: string;
  status: string;
  created_at: string;
}

interface Stats {
  total_bids: number;
  submitted: number;
  won: number;
  win_rate: number;
  total_value: number;
}

export default function FreelanceBids() {
  const [bids, setBids] = useState<Bid[]>([]);
  const [stats, setStats] = useState<Stats | null>(null);
  const [loading, setLoading] = useState(true);
  const [platformFilter, setPlatformFilter] = useState('');
  const [statusFilter, setStatusFilter] = useState('');
  const [showBidForm, setShowBidForm] = useState(false);
  const [bidForm, setBidForm] = useState({ platform: 'upwork', project_title: '', project_url: '', client_description: '', required_skills: '', budget_range: '', deadline: '' });
  const [selectedBid, setSelectedBid] = useState<string | null>(null);

  const load = () => {
    Promise.all([
      freelanceApi.getBids(platformFilter || undefined, statusFilter || undefined).then(r => { const d = r.data?.bids ?? r.data; setBids(Array.isArray(d) ? d : []); }).catch(() => {}),
      freelanceApi.getStats().then(r => setStats(r.data)).catch(() => {}),
    ]).finally(() => setLoading(false));
  };

  useEffect(() => { load(); }, [platformFilter, statusFilter]);

  const createBid = () => {
    if (!bidForm.project_title.trim()) return;
    freelanceApi.createBid({
      platform: bidForm.platform,
      project_title: bidForm.project_title,
      project_url: bidForm.project_url || undefined,
      description: bidForm.client_description,
      required_skills: bidForm.required_skills ? bidForm.required_skills.split(',').map(s => s.trim()) : [],
      budget_range: bidForm.budget_range || undefined,
    })
      .then(() => { setShowBidForm(false); setBidForm({ platform: 'upwork', project_title: '', project_url: '', client_description: '', required_skills: '', budget_range: '', deadline: '' }); load(); })
      .catch(() => {});
  };

  const submitBid = (id: string) => {
    freelanceApi.submitBid(id).then(() => load()).catch(() => {});
  };

  const updateStatus = (id: string, status: string) => {
    freelanceApi.updateBidStatus(id, status).then(() => load()).catch(() => {});
  };

  if (loading) return <LoadingSpinner text="Loading freelance bids..." />;

  const platforms = ['upwork', 'freelancer', 'toptal', 'fiverr'];
  const statusOptions = ['draft', 'submitted', 'won', 'lost', 'withdrawn'];
  const statusColors: Record<string, 'gold' | 'cyan' | 'green' | 'red' | 'purple'> = {
    draft: 'gold', submitted: 'cyan', won: 'green', lost: 'red', withdrawn: 'purple'
  };
  const platformIcons: Record<string, string> = { upwork: '🟢', freelancer: '🔵', toptal: '🟣', fiverr: '🟡' };

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="page-title">Freelance Bidding</h1>
          <p className="text-gray-400 text-sm mt-1">AI-powered proposal generation & bid management</p>
        </div>
        <button onClick={() => setShowBidForm(!showBidForm)} className="btn-primary">
          + New Bid
        </button>
      </div>

      {/* Stats */}
      {stats && (
        <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
          <StatCard label="Total Bids" value={stats.total_bids} icon="📝" />
          <StatCard label="Submitted" value={stats.submitted} icon="📤" />
          <StatCard label="Won" value={stats.won} icon="🏆" />
          <StatCard label="Win Rate" value={`${Math.round((stats.win_rate ?? 0) * 100)}%`} icon="📈" />
          <StatCard label="Total Value" value={`$${((stats.total_value ?? 0) / 1000).toFixed(1)}k`} icon="💰" />
        </div>
      )}

      {/* Bid Form */}
      {showBidForm && (
        <div className="card p-6 space-y-4">
          <h3 className="text-white font-medium">Create New Bid</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <select value={bidForm.platform} onChange={e => setBidForm({...bidForm, platform: e.target.value})} className="input-field">
              {platforms.map(p => <option key={p} value={p}>{p.charAt(0).toUpperCase() + p.slice(1)}</option>)}
            </select>
            <input type="text" value={bidForm.project_title} onChange={e => setBidForm({...bidForm, project_title: e.target.value})} placeholder="Project title" className="input-field" />
            <input type="text" value={bidForm.project_url} onChange={e => setBidForm({...bidForm, project_url: e.target.value})} placeholder="Project URL" className="input-field" />
            <input type="text" value={bidForm.budget_range} onChange={e => setBidForm({...bidForm, budget_range: e.target.value})} placeholder="Budget range (e.g. $500-$1000)" className="input-field" />
            <input type="text" value={bidForm.required_skills} onChange={e => setBidForm({...bidForm, required_skills: e.target.value})} placeholder="Skills (comma separated)" className="input-field" />
            <input type="text" value={bidForm.deadline} onChange={e => setBidForm({...bidForm, deadline: e.target.value})} placeholder="Deadline" className="input-field" />
          </div>
          <textarea value={bidForm.client_description} onChange={e => setBidForm({...bidForm, client_description: e.target.value})} placeholder="Client/project description..." className="input-field w-full h-24 resize-none" />
          <div className="flex gap-3">
            <button onClick={createBid} className="btn-primary">Create Bid</button>
            <button onClick={() => setShowBidForm(false)} className="px-4 py-2 text-sm text-gray-400 hover:text-gray-200 transition-colors">Cancel</button>
          </div>
        </div>
      )}

      {/* Filters */}
      <div className="flex gap-4 flex-wrap">
        <div className="flex gap-2">
          <span className="text-xs text-gray-500 self-center">Platform:</span>
          <button onClick={() => setPlatformFilter('')} className={`px-3 py-1.5 rounded-xl text-xs font-medium transition-all ${!platformFilter ? 'bg-cyan-400/10 text-cyan-400 border border-cyan-400/30' : 'bg-surface text-gray-400 border border-transparent'}`}>All</button>
          {platforms.map(p => (
            <button key={p} onClick={() => setPlatformFilter(platformFilter === p ? '' : p)} className={`px-3 py-1.5 rounded-xl text-xs font-medium transition-all capitalize ${platformFilter === p ? 'bg-cyan-400/10 text-cyan-400 border border-cyan-400/30' : 'bg-surface text-gray-400 border border-transparent'}`}>
              {platformIcons[p]} {p}
            </button>
          ))}
        </div>
        <div className="flex gap-2">
          <span className="text-xs text-gray-500 self-center">Status:</span>
          <button onClick={() => setStatusFilter('')} className={`px-3 py-1.5 rounded-xl text-xs font-medium transition-all ${!statusFilter ? 'bg-cyan-400/10 text-cyan-400 border border-cyan-400/30' : 'bg-surface text-gray-400 border border-transparent'}`}>All</button>
          {statusOptions.map(s => (
            <button key={s} onClick={() => setStatusFilter(statusFilter === s ? '' : s)} className={`px-3 py-1.5 rounded-xl text-xs font-medium transition-all capitalize ${statusFilter === s ? 'bg-cyan-400/10 text-cyan-400 border border-cyan-400/30' : 'bg-surface text-gray-400 border border-transparent'}`}>
              {s}
            </button>
          ))}
        </div>
      </div>

      {/* Bids List */}
      <div className="space-y-3">
        {bids.length === 0 ? (
          <EmptyState title="No bids found" description="Create your first bid to get AI-generated proposals" />
        ) : (
          bids.map(bid => (
            <div key={bid.id} className="card p-4 cursor-pointer hover:border-cyan-400/30 transition-all" onClick={() => setSelectedBid(selectedBid === bid.id ? null : bid.id)}>
              <div className="flex items-center justify-between">
                <div>
                  <div className="flex items-center gap-2">
                    <span>{platformIcons[bid.platform] ?? '📋'}</span>
                    <h3 className="text-white font-medium">{bid.project_title}</h3>
                    <Badge variant={statusColors[bid.status] ?? 'gold'}>{bid.status}</Badge>
                  </div>
                  <p className="text-gray-400 text-sm mt-0.5 capitalize">{bid.platform} · {bid.estimated_hours}h estimated</p>
                </div>
                <div className="text-right">
                  <div className="text-lg font-bold text-cyan-400">${bid.bid_amount?.toLocaleString()}</div>
                  <div className="text-xs text-gray-500">{new Date(bid.created_at).toLocaleDateString()}</div>
                </div>
              </div>
              {selectedBid === bid.id && (
                <div className="mt-4 space-y-3">
                  {bid.proposal_text && (
                    <div>
                      <h4 className="text-xs text-gray-500 uppercase tracking-wide mb-2">AI-Generated Proposal</h4>
                      <p className="text-sm text-gray-300 bg-navy-800/50 rounded-lg p-3 whitespace-pre-line">{bid.proposal_text}</p>
                    </div>
                  )}
                  <div className="flex gap-2">
                    {bid.status === 'draft' && (
                      <button onClick={(e) => { e.stopPropagation(); submitBid(bid.id); }} className="text-xs px-3 py-1.5 rounded-lg bg-cyan-400/10 text-cyan-400 hover:bg-cyan-400/20 transition-all">Submit Bid</button>
                    )}
                    {bid.status === 'submitted' && (
                      <>
                        <button onClick={(e) => { e.stopPropagation(); updateStatus(bid.id, 'won'); }} className="text-xs px-3 py-1.5 rounded-lg bg-green-400/10 text-green-400 hover:bg-green-400/20 transition-all">Won</button>
                        <button onClick={(e) => { e.stopPropagation(); updateStatus(bid.id, 'lost'); }} className="text-xs px-3 py-1.5 rounded-lg bg-red-400/10 text-red-400 hover:bg-red-400/20 transition-all">Lost</button>
                      </>
                    )}
                    {bid.project_url && (
                      <a href={bid.project_url} target="_blank" rel="noopener noreferrer" onClick={e => e.stopPropagation()} className="text-xs px-3 py-1.5 rounded-lg bg-purple-400/10 text-purple-400 hover:bg-purple-400/20 transition-all">View Project ↗</a>
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
