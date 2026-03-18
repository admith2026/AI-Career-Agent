'use client';

import { useEffect, useState } from 'react';
import { contentApi } from '@/lib/api';
import { Badge, LoadingSpinner, StatCard, EmptyState } from '@/components/ui';

interface Post {
  id: string;
  platform: string;
  content_type: string;
  title: string;
  body: string;
  hashtags: string[];
  status: string;
  scheduled_for: string | null;
  likes: number;
  shares: number;
  comments: number;
  impressions: number;
  created_at: string;
}

interface CalendarItem {
  date: string;
  posts: { id: string; title: string; platform: string; status: string }[];
}

interface Stats {
  total_posts: number;
  published: number;
  total_engagement: number;
  avg_impressions: number;
}

export default function DemandGeneration() {
  const [posts, setPosts] = useState<Post[]>([]);
  const [stats, setStats] = useState<Stats | null>(null);
  const [calendar, setCalendar] = useState<CalendarItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [tab, setTab] = useState<'posts' | 'calendar'>('posts');
  const [platformFilter, setPlatformFilter] = useState('');
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [createForm, setCreateForm] = useState({ platform: 'linkedin', content_type: 'thought_leadership', topic: '', key_points: '' });
  const [selectedPost, setSelectedPost] = useState<string | null>(null);

  const load = () => {
    Promise.all([
      contentApi.getPosts(platformFilter || undefined).then(r => { const d = r.data?.posts ?? r.data; setPosts(Array.isArray(d) ? d : []); }).catch(() => {}),
      contentApi.getStats().then(r => setStats(r.data)).catch(() => {}),
      contentApi.getCalendar(14).then(r => { const d = r.data?.calendar ?? r.data; setCalendar(Array.isArray(d) ? d : []); }).catch(() => {}),
    ]).finally(() => setLoading(false));
  };

  useEffect(() => { load(); }, [platformFilter]);

  const generateContent = () => {
    if (!createForm.topic.trim()) return;
    contentApi.generate({
      ...createForm,
      key_points: createForm.key_points ? createForm.key_points.split(',').map(s => s.trim()) : [],
    })
      .then(() => { setShowCreateForm(false); setCreateForm({ platform: 'linkedin', content_type: 'thought_leadership', topic: '', key_points: '' }); load(); })
      .catch(() => {});
  };

  const updateStatus = (id: string, status: string) => {
    contentApi.updatePostStatus(id, status).then(() => load()).catch(() => {});
  };

  if (loading) return <LoadingSpinner text="Loading content engine..." />;

  const platforms = ['linkedin', 'twitter', 'dev.to', 'medium'];
  const contentTypes = ['thought_leadership', 'technical', 'career_insight', 'industry_news', 'project_showcase'];
  const statusColors: Record<string, 'gold' | 'cyan' | 'green' | 'purple' | 'red'> = {
    draft: 'gold', scheduled: 'cyan', published: 'green', archived: 'purple'
  };
  const platformIcons: Record<string, string> = { linkedin: '💼', twitter: '🐦', 'dev.to': '👩‍💻', medium: '📝' };

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="page-title">Demand Generation</h1>
          <p className="text-gray-400 text-sm mt-1">AI content creation, scheduling & engagement tracking</p>
        </div>
        <button onClick={() => setShowCreateForm(!showCreateForm)} className="btn-primary">
          + Generate Content
        </button>
      </div>

      {/* Stats */}
      {stats && (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <StatCard label="Total Posts" value={stats.total_posts} icon="📝" />
          <StatCard label="Published" value={stats.published} icon="✅" />
          <StatCard label="Engagement" value={stats.total_engagement} icon="💬" />
          <StatCard label="Avg Impressions" value={stats.avg_impressions} icon="👁" />
        </div>
      )}

      {/* Create Form */}
      {showCreateForm && (
        <div className="card p-6 space-y-4">
          <h3 className="text-white font-medium">Generate Content</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <select value={createForm.platform} onChange={e => setCreateForm({...createForm, platform: e.target.value})} className="input-field">
              {platforms.map(p => <option key={p} value={p}>{platformIcons[p]} {p.charAt(0).toUpperCase() + p.slice(1)}</option>)}
            </select>
            <select value={createForm.content_type} onChange={e => setCreateForm({...createForm, content_type: e.target.value})} className="input-field">
              {contentTypes.map(t => <option key={t} value={t}>{t.replace(/_/g, ' ')}</option>)}
            </select>
            <input type="text" value={createForm.topic} onChange={e => setCreateForm({...createForm, topic: e.target.value})} placeholder="Topic" className="input-field" />
            <input type="text" value={createForm.key_points} onChange={e => setCreateForm({...createForm, key_points: e.target.value})} placeholder="Key points (comma separated)" className="input-field" />
          </div>
          <div className="flex gap-3">
            <button onClick={generateContent} className="btn-primary">Generate</button>
            <button onClick={() => setShowCreateForm(false)} className="px-4 py-2 text-sm text-gray-400 hover:text-gray-200 transition-colors">Cancel</button>
          </div>
        </div>
      )}

      {/* Tabs */}
      <div className="flex gap-2 border-b border-gray-700/30 pb-2">
        <button onClick={() => setTab('posts')} className={`px-4 py-2 rounded-t-lg text-sm font-medium transition-all ${tab === 'posts' ? 'bg-cyan-400/10 text-cyan-400 border-b-2 border-cyan-400' : 'text-gray-400 hover:text-gray-200'}`}>
          Posts
        </button>
        <button onClick={() => setTab('calendar')} className={`px-4 py-2 rounded-t-lg text-sm font-medium transition-all ${tab === 'calendar' ? 'bg-cyan-400/10 text-cyan-400 border-b-2 border-cyan-400' : 'text-gray-400 hover:text-gray-200'}`}>
          Calendar
        </button>
      </div>

      {/* Posts Tab */}
      {tab === 'posts' && (
        <>
          {/* Platform Filters */}
          <div className="flex gap-2 flex-wrap">
            <button onClick={() => setPlatformFilter('')} className={`px-3 py-1.5 rounded-xl text-xs font-medium transition-all ${!platformFilter ? 'bg-cyan-400/10 text-cyan-400 border border-cyan-400/30' : 'bg-surface text-gray-400 border border-transparent'}`}>All</button>
            {platforms.map(p => (
              <button key={p} onClick={() => setPlatformFilter(platformFilter === p ? '' : p)} className={`px-3 py-1.5 rounded-xl text-xs font-medium transition-all capitalize ${platformFilter === p ? 'bg-cyan-400/10 text-cyan-400 border border-cyan-400/30' : 'bg-surface text-gray-400 border border-transparent'}`}>
                {platformIcons[p]} {p}
              </button>
            ))}
          </div>

          {/* Posts List */}
          <div className="space-y-3">
            {posts.length === 0 ? (
              <EmptyState title="No content yet" description="Generate your first AI-powered content piece" />
            ) : (
              posts.map(post => (
                <div key={post.id} className="card p-4 cursor-pointer hover:border-cyan-400/30 transition-all" onClick={() => setSelectedPost(selectedPost === post.id ? null : post.id)}>
                  <div className="flex items-center justify-between">
                    <div>
                      <div className="flex items-center gap-2">
                        <span>{platformIcons[post.platform] ?? '📋'}</span>
                        <h3 className="text-white font-medium">{post.title}</h3>
                        <Badge variant={statusColors[post.status] ?? 'gold'}>{post.status}</Badge>
                      </div>
                      <p className="text-gray-400 text-sm mt-0.5 capitalize">{post.platform} · {post.content_type?.replace(/_/g, ' ')}</p>
                    </div>
                    <div className="text-right">
                      {post.status === 'published' && (
                        <div className="flex items-center gap-3 text-xs text-gray-400">
                          <span>❤️ {post.likes}</span>
                          <span>🔄 {post.shares}</span>
                          <span>💬 {post.comments}</span>
                        </div>
                      )}
                      <div className="text-xs text-gray-500 mt-1">{new Date(post.created_at).toLocaleDateString()}</div>
                    </div>
                  </div>
                  {selectedPost === post.id && (
                    <div className="mt-4 space-y-3">
                      {post.body && (
                        <div className="text-sm text-gray-300 bg-navy-800/50 rounded-lg p-3 whitespace-pre-line">{post.body}</div>
                      )}
                      {post.hashtags?.length > 0 && (
                        <div className="flex gap-2 flex-wrap">
                          {post.hashtags.map((h, i) => (
                            <span key={i} className="text-xs px-2 py-0.5 rounded-full bg-cyan-400/10 text-cyan-400">#{h}</span>
                          ))}
                        </div>
                      )}
                      {post.impressions > 0 && (
                        <div className="grid grid-cols-4 gap-3">
                          <div className="bg-navy-800/50 rounded-lg p-2 text-center">
                            <div className="text-xs text-gray-500">Likes</div>
                            <div className="text-sm font-bold text-red-400">{post.likes}</div>
                          </div>
                          <div className="bg-navy-800/50 rounded-lg p-2 text-center">
                            <div className="text-xs text-gray-500">Shares</div>
                            <div className="text-sm font-bold text-cyan-400">{post.shares}</div>
                          </div>
                          <div className="bg-navy-800/50 rounded-lg p-2 text-center">
                            <div className="text-xs text-gray-500">Comments</div>
                            <div className="text-sm font-bold text-green-400">{post.comments}</div>
                          </div>
                          <div className="bg-navy-800/50 rounded-lg p-2 text-center">
                            <div className="text-xs text-gray-500">Impressions</div>
                            <div className="text-sm font-bold text-purple-400">{post.impressions}</div>
                          </div>
                        </div>
                      )}
                      <div className="flex gap-2">
                        {post.status === 'draft' && <button onClick={(e) => { e.stopPropagation(); updateStatus(post.id, 'scheduled'); }} className="text-xs px-3 py-1.5 rounded-lg bg-cyan-400/10 text-cyan-400 hover:bg-cyan-400/20 transition-all">Schedule</button>}
                        {post.status === 'scheduled' && <button onClick={(e) => { e.stopPropagation(); updateStatus(post.id, 'published'); }} className="text-xs px-3 py-1.5 rounded-lg bg-green-400/10 text-green-400 hover:bg-green-400/20 transition-all">Publish Now</button>}
                        {post.status !== 'archived' && <button onClick={(e) => { e.stopPropagation(); updateStatus(post.id, 'archived'); }} className="text-xs px-3 py-1.5 rounded-lg bg-red-400/10 text-red-400 hover:bg-red-400/20 transition-all">Archive</button>}
                      </div>
                    </div>
                  )}
                </div>
              ))
            )}
          </div>
        </>
      )}

      {/* Calendar Tab */}
      {tab === 'calendar' && (
        <div className="space-y-3">
          {calendar.length === 0 ? (
            <EmptyState title="No scheduled content" description="Schedule posts to see them on the calendar" />
          ) : (
            calendar.map((day, i) => (
              <div key={i} className="card p-4">
                <div className="text-xs text-gray-500 uppercase tracking-wide mb-3">{new Date(day.date).toLocaleDateString('en-US', { weekday: 'long', month: 'short', day: 'numeric' })}</div>
                {day.posts?.length > 0 ? (
                  <div className="space-y-2">
                    {day.posts.map((p, j) => (
                      <div key={j} className="flex items-center justify-between p-2 bg-navy-800/50 rounded-lg">
                        <div className="flex items-center gap-2">
                          <span>{platformIcons[p.platform] ?? '📋'}</span>
                          <span className="text-sm text-white">{p.title}</span>
                        </div>
                        <Badge variant={statusColors[p.status] ?? 'gold'}>{p.status}</Badge>
                      </div>
                    ))}
                  </div>
                ) : (
                  <p className="text-sm text-gray-500 italic">No posts scheduled</p>
                )}
              </div>
            ))
          )}
        </div>
      )}
    </div>
  );
}
