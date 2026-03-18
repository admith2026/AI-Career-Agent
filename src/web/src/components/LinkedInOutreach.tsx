'use client';

import { useEffect, useState } from 'react';
import { linkedinApi } from '@/lib/api';
import { Badge, LoadingSpinner, StatCard, EmptyState } from '@/components/ui';

interface OutreachItem {
  id: string;
  recruiter_name: string;
  company: string;
  action_type: string;
  status: string;
  message_text: string;
  created_at: string;
  replied_at: string | null;
}

interface Stats {
  total_sent: number;
  total_replies: number;
  reply_rate: number;
  pending: number;
}

export default function LinkedInOutreach() {
  const [items, setItems] = useState<OutreachItem[]>([]);
  const [stats, setStats] = useState<Stats | null>(null);
  const [loading, setLoading] = useState(true);
  const [statusFilter, setStatusFilter] = useState('');
  const [showConnectForm, setShowConnectForm] = useState(false);
  const [connectForm, setConnectForm] = useState({ recruiter_contact_id: '', recruiter_name: '', company: '', title: '' });

  const load = () => {
    Promise.all([
      linkedinApi.getOutreach(statusFilter || undefined).then(r => { const d = r.data?.outreach ?? r.data; setItems(Array.isArray(d) ? d : []); }).catch(() => {}),
      linkedinApi.getStats().then(r => setStats(r.data)).catch(() => {}),
    ]).finally(() => setLoading(false));
  };

  useEffect(() => { load(); }, [statusFilter]);

  const handleConnect = () => {
    if (!connectForm.recruiter_name.trim()) return;
    linkedinApi.connect(connectForm)
      .then(() => { setShowConnectForm(false); setConnectForm({ recruiter_contact_id: '', recruiter_name: '', company: '', title: '' }); load(); })
      .catch(() => {});
  };

  const markReplied = (id: string) => {
    linkedinApi.markReplied(id).then(() => load()).catch(() => {});
  };

  if (loading) return <LoadingSpinner text="Loading LinkedIn outreach..." />;

  const statuses = ['pending', 'sent', 'replied', 'accepted'];

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="page-title">LinkedIn Automation</h1>
          <p className="text-gray-400 text-sm mt-1">Automated recruiter outreach & connection management</p>
        </div>
        <button onClick={() => setShowConnectForm(!showConnectForm)} className="btn-primary">
          + New Connection
        </button>
      </div>

      {/* Stats */}
      {stats && (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <StatCard label="Total Sent" value={stats.total_sent} icon="📤" />
          <StatCard label="Replies" value={stats.total_replies} icon="💬" />
          <StatCard label="Reply Rate" value={`${Math.round((stats.reply_rate ?? 0) * 100)}%`} icon="📈" />
          <StatCard label="Pending" value={stats.pending} icon="⏳" />
        </div>
      )}

      {/* Connect Form */}
      {showConnectForm && (
        <div className="card p-6 space-y-4">
          <h3 className="text-white font-medium">Send Connection Request</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <input type="text" value={connectForm.recruiter_name} onChange={e => setConnectForm({...connectForm, recruiter_name: e.target.value})} placeholder="Recruiter name" className="input-field" />
            <input type="text" value={connectForm.company} onChange={e => setConnectForm({...connectForm, company: e.target.value})} placeholder="Company" className="input-field" />
            <input type="text" value={connectForm.title} onChange={e => setConnectForm({...connectForm, title: e.target.value})} placeholder="Title / Role" className="input-field" />
            <input type="text" value={connectForm.recruiter_contact_id} onChange={e => setConnectForm({...connectForm, recruiter_contact_id: e.target.value})} placeholder="Contact ID (optional)" className="input-field" />
          </div>
          <div className="flex gap-3">
            <button onClick={handleConnect} className="btn-primary">Send Request</button>
            <button onClick={() => setShowConnectForm(false)} className="px-4 py-2 text-sm text-gray-400 hover:text-gray-200 transition-colors">Cancel</button>
          </div>
        </div>
      )}

      {/* Filters */}
      <div className="flex gap-2 flex-wrap">
        <button onClick={() => setStatusFilter('')} className={`px-3 py-1.5 rounded-xl text-xs font-medium transition-all ${!statusFilter ? 'bg-cyan-400/10 text-cyan-400 border border-cyan-400/30' : 'bg-surface text-gray-400 border border-transparent'}`}>
          All
        </button>
        {statuses.map(s => (
          <button key={s} onClick={() => setStatusFilter(statusFilter === s ? '' : s)} className={`px-3 py-1.5 rounded-xl text-xs font-medium transition-all capitalize ${statusFilter === s ? 'bg-cyan-400/10 text-cyan-400 border border-cyan-400/30' : 'bg-surface text-gray-400 border border-transparent'}`}>
            {s}
          </button>
        ))}
      </div>

      {/* Outreach List */}
      <div className="space-y-3">
        {items.length === 0 ? (
          <EmptyState title="No outreach yet" description="Start connecting with recruiters to see activity here" />
        ) : (
          items.map(item => (
            <div key={item.id} className="card p-4">
              <div className="flex items-center justify-between">
                <div>
                  <div className="flex items-center gap-2">
                    <h3 className="text-white font-medium">{item.recruiter_name}</h3>
                    <Badge variant={item.status === 'replied' ? 'green' : item.status === 'sent' ? 'cyan' : item.status === 'accepted' ? 'purple' : 'gold'}>{item.status}</Badge>
                  </div>
                  <p className="text-gray-400 text-sm mt-0.5">{item.company} · {item.action_type}</p>
                </div>
                <div className="flex items-center gap-2">
                  {item.status === 'sent' && (
                    <button onClick={() => markReplied(item.id)} className="text-xs px-3 py-1.5 rounded-lg bg-green-400/10 text-green-400 hover:bg-green-400/20 transition-all">
                      Mark Replied
                    </button>
                  )}
                  <span className="text-xs text-gray-500">{new Date(item.created_at).toLocaleDateString()}</span>
                </div>
              </div>
              {item.message_text && (
                <p className="mt-2 text-sm text-gray-300 bg-navy-800/50 rounded-lg p-3 line-clamp-2">{item.message_text}</p>
              )}
            </div>
          ))
        )}
      </div>
    </div>
  );
}
