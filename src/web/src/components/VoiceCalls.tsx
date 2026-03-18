'use client';

import { useEffect, useState } from 'react';
import { voiceApi } from '@/lib/api';
import { Badge, LoadingSpinner, StatCard, EmptyState } from '@/components/ui';

interface Call {
  id: string;
  recruiter_name: string;
  phone_number: string;
  status: string;
  duration_seconds: number;
  outcome: string;
  transcript_summary: string;
  scheduled_at: string;
  created_at: string;
}

interface Stats {
  total_calls: number;
  completed: number;
  avg_duration: number;
  positive_outcomes: number;
}

export default function VoiceCalls() {
  const [calls, setCalls] = useState<Call[]>([]);
  const [stats, setStats] = useState<Stats | null>(null);
  const [loading, setLoading] = useState(true);
  const [showCallForm, setShowCallForm] = useState(false);
  const [callForm, setCallForm] = useState({ recruiter_contact_id: '', phone_number: '', purpose: 'follow_up' });
  const [selectedCall, setSelectedCall] = useState<Call | null>(null);

  const load = () => {
    Promise.all([
      voiceApi.getCalls().then(r => { const d = r.data?.calls ?? r.data; setCalls(Array.isArray(d) ? d : []); }).catch(() => {}),
      voiceApi.getStats().then(r => setStats(r.data)).catch(() => {}),
    ]).finally(() => setLoading(false));
  };

  useEffect(() => { load(); }, []);

  const initiateCall = () => {
    if (!callForm.phone_number.trim()) return;
    voiceApi.initiateCall(callForm)
      .then(() => { setShowCallForm(false); setCallForm({ recruiter_contact_id: '', phone_number: '', purpose: 'follow_up' }); load(); })
      .catch(() => {});
  };

  if (loading) return <LoadingSpinner text="Loading voice calls..." />;

  const outcomeColors: Record<string, 'green' | 'cyan' | 'gold' | 'red' | 'purple'> = {
    positive: 'green', follow_up: 'cyan', no_answer: 'gold', declined: 'red', scheduled: 'purple'
  };

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="page-title">Voice AI</h1>
          <p className="text-gray-400 text-sm mt-1">AI-powered voice calls with recruiters via Twilio</p>
        </div>
        <button onClick={() => setShowCallForm(!showCallForm)} className="btn-primary">
          📞 New Call
        </button>
      </div>

      {/* Stats */}
      {stats && (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <StatCard label="Total Calls" value={stats.total_calls} icon="📞" />
          <StatCard label="Completed" value={stats.completed} icon="✅" />
          <StatCard label="Avg Duration" value={`${Math.round(stats.avg_duration ?? 0)}s`} icon="⏱" />
          <StatCard label="Positive Outcomes" value={stats.positive_outcomes} icon="🎉" />
        </div>
      )}

      {/* Call Form */}
      {showCallForm && (
        <div className="card p-6 space-y-4">
          <h3 className="text-white font-medium">Initiate Voice Call</h3>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <input type="text" value={callForm.phone_number} onChange={e => setCallForm({...callForm, phone_number: e.target.value})} placeholder="Phone number" className="input-field" />
            <input type="text" value={callForm.recruiter_contact_id} onChange={e => setCallForm({...callForm, recruiter_contact_id: e.target.value})} placeholder="Contact ID (optional)" className="input-field" />
            <select value={callForm.purpose} onChange={e => setCallForm({...callForm, purpose: e.target.value})} className="input-field">
              <option value="follow_up">Follow Up</option>
              <option value="introduction">Introduction</option>
              <option value="interview_schedule">Schedule Interview</option>
              <option value="offer_discussion">Offer Discussion</option>
            </select>
          </div>
          <div className="flex gap-3">
            <button onClick={initiateCall} className="btn-primary">Start Call</button>
            <button onClick={() => setShowCallForm(false)} className="px-4 py-2 text-sm text-gray-400 hover:text-gray-200 transition-colors">Cancel</button>
          </div>
        </div>
      )}

      {/* Call List */}
      <div className="space-y-3">
        {calls.length === 0 ? (
          <EmptyState title="No calls yet" description="Initiate your first AI-powered call to get started" />
        ) : (
          calls.map(call => (
            <div key={call.id} className="card p-4 cursor-pointer hover:border-cyan-400/30 transition-all" onClick={() => setSelectedCall(selectedCall?.id === call.id ? null : call)}>
              <div className="flex items-center justify-between">
                <div>
                  <div className="flex items-center gap-2">
                    <h3 className="text-white font-medium">{call.recruiter_name || 'Unknown'}</h3>
                    <Badge variant={call.status === 'completed' ? 'green' : call.status === 'in_progress' ? 'cyan' : 'gold'}>{call.status}</Badge>
                    {call.outcome && <Badge variant={outcomeColors[call.outcome] ?? 'gold'}>{call.outcome}</Badge>}
                  </div>
                  <p className="text-gray-400 text-sm mt-0.5">{call.phone_number}</p>
                </div>
                <div className="text-right">
                  {call.duration_seconds > 0 && <div className="text-sm text-cyan-400">{Math.floor(call.duration_seconds / 60)}m {call.duration_seconds % 60}s</div>}
                  <div className="text-xs text-gray-500">{new Date(call.created_at).toLocaleDateString()}</div>
                </div>
              </div>
              {selectedCall?.id === call.id && call.transcript_summary && (
                <div className="mt-3 p-3 bg-navy-800/50 rounded-lg">
                  <div className="text-xs text-gray-500 mb-1">Transcript Summary</div>
                  <p className="text-sm text-gray-300">{call.transcript_summary}</p>
                </div>
              )}
            </div>
          ))
        )}
      </div>
    </div>
  );
}
