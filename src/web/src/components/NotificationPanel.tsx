'use client';

import { useState } from 'react';
import { Badge } from '@/components/ui';

interface Notification {
  id: string;
  type: 'job_match' | 'application' | 'signal' | 'system' | 'reminder';
  title: string;
  message: string;
  time: string;
  read: boolean;
}

const typeConfig: Record<string, { icon: string; color: string }> = {
  job_match: { icon: '💼', color: 'bg-cyan-500/20 text-cyan-400' },
  application: { icon: '📋', color: 'bg-green-500/20 text-green-400' },
  signal: { icon: '📡', color: 'bg-purple-500/20 text-purple-400' },
  system: { icon: '⚙️', color: 'bg-gray-500/20 text-gray-400' },
  reminder: { icon: '⏰', color: 'bg-gold-400/20 text-gold-400' },
};

const MOCK_NOTIFICATIONS: Notification[] = [
  { id: '1', type: 'job_match', title: 'New high-match job!', message: 'Senior Python Developer at Stripe — 95% match', time: '2m ago', read: false },
  { id: '2', type: 'application', title: 'Application update', message: 'Your application to Figma moved to Interview stage', time: '15m ago', read: false },
  { id: '3', type: 'signal', title: 'Hiring signal detected', message: 'Vercel just raised $150M — expecting 20+ new roles', time: '1h ago', read: false },
  { id: '4', type: 'reminder', title: 'Follow-up reminder', message: 'Follow up with DataDog recruiter — applied 5 days ago', time: '2h ago', read: true },
  { id: '5', type: 'job_match', title: '3 new matches', message: 'Morning digest: 3 jobs above 85% match score', time: '6h ago', read: true },
  { id: '6', type: 'system', title: 'Crawl complete', message: 'Discovered 47 new jobs from 5 sources', time: '8h ago', read: true },
];

interface NotificationPanelProps {
  open: boolean;
  onClose: () => void;
}

export default function NotificationPanel({ open, onClose }: NotificationPanelProps) {
  const [notifications, setNotifications] = useState(MOCK_NOTIFICATIONS);
  const [filter, setFilter] = useState<string | null>(null);

  if (!open) return null;

  const unreadCount = notifications.filter((n) => !n.read).length;
  const filtered = filter ? notifications.filter((n) => n.type === filter) : notifications;

  const markAllRead = () => {
    setNotifications((prev) => prev.map((n) => ({ ...n, read: true })));
  };

  const markRead = (id: string) => {
    setNotifications((prev) => prev.map((n) => n.id === id ? { ...n, read: true } : n));
  };

  return (
    <>
      <div className="fixed inset-0 z-40" onClick={onClose} />
      <div className="fixed right-6 top-4 z-50 w-[380px] max-h-[580px] flex flex-col bg-navy-900 border border-gray-700/40 rounded-2xl shadow-2xl animate-slide-up overflow-hidden">
        {/* Header */}
        <div className="p-4 border-b border-gray-700/30">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <h3 className="text-sm font-semibold text-white">Notifications</h3>
              {unreadCount > 0 && (
                <span className="px-1.5 py-0.5 rounded-full bg-cyan-500/20 text-cyan-400 text-[10px] font-bold">{unreadCount}</span>
              )}
            </div>
            <div className="flex items-center gap-2">
              {unreadCount > 0 && (
                <button onClick={markAllRead} className="text-[11px] text-cyan-400 hover:text-cyan-300 transition-colors">
                  Mark all read
                </button>
              )}
              <button onClick={onClose} className="text-gray-500 hover:text-white transition-colors">
                <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>
          </div>
          {/* Type filter */}
          <div className="flex gap-1.5 mt-3">
            <button
              onClick={() => setFilter(null)}
              className={`px-2 py-1 rounded-lg text-[10px] font-medium transition-all ${!filter ? 'bg-cyan-500/20 text-cyan-400' : 'text-gray-500 hover:text-gray-300'}`}
            >
              All
            </button>
            {Object.entries(typeConfig).map(([key, cfg]) => (
              <button
                key={key}
                onClick={() => setFilter(filter === key ? null : key)}
                className={`px-2 py-1 rounded-lg text-[10px] font-medium transition-all flex items-center gap-1 ${filter === key ? 'bg-cyan-500/20 text-cyan-400' : 'text-gray-500 hover:text-gray-300'}`}
              >
                <span className="text-xs">{cfg.icon}</span>
              </button>
            ))}
          </div>
        </div>

        {/* Notification List */}
        <div className="flex-1 overflow-y-auto">
          {filtered.length === 0 ? (
            <div className="p-8 text-center">
              <p className="text-gray-500 text-sm">No notifications</p>
            </div>
          ) : (
            <div className="divide-y divide-gray-700/20">
              {filtered.map((n) => {
                const cfg = typeConfig[n.type] ?? typeConfig.system;
                return (
                  <div
                    key={n.id}
                    onClick={() => markRead(n.id)}
                    className={`p-4 flex items-start gap-3 cursor-pointer transition-colors hover:bg-navy-800/50 ${!n.read ? 'bg-cyan-500/[0.03]' : ''}`}
                  >
                    <div className={`w-9 h-9 rounded-xl flex items-center justify-center flex-shrink-0 text-base ${cfg.color}`}>
                      {cfg.icon}
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2">
                        <p className={`text-sm font-medium truncate ${!n.read ? 'text-white' : 'text-gray-400'}`}>{n.title}</p>
                        {!n.read && <span className="w-2 h-2 rounded-full bg-cyan-400 flex-shrink-0" />}
                      </div>
                      <p className="text-xs text-gray-500 mt-0.5 line-clamp-2">{n.message}</p>
                      <p className="text-[10px] text-gray-600 mt-1">{n.time}</p>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="p-3 border-t border-gray-700/30 text-center">
          <button className="text-xs text-cyan-400 hover:text-cyan-300 transition-colors">
            View All Notifications →
          </button>
        </div>
      </div>
    </>
  );
}

/** Bell icon button for triggering notifications */
export function NotificationBell({ count, onClick }: { count: number; onClick: () => void }) {
  return (
    <button onClick={onClick} className="relative p-2 rounded-xl hover:bg-navy-800 transition-colors group">
      <svg className="w-5 h-5 text-gray-400 group-hover:text-white transition-colors" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9" />
      </svg>
      {count > 0 && (
        <span className="absolute -top-0.5 -right-0.5 w-4 h-4 rounded-full bg-red-500 text-[9px] font-bold text-white flex items-center justify-center animate-pulse">
          {count > 9 ? '9+' : count}
        </span>
      )}
    </button>
  );
}
