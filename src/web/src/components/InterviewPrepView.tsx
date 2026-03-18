'use client';

import { useEffect, useState } from 'react';
import { interviewApi } from '@/lib/api';
import { Badge, LoadingSpinner, StatCard, EmptyState } from '@/components/ui';

interface Prep {
  id: string;
  job_title: string;
  company_name: string;
  difficulty_level: string;
  questions: { question: string; category: string; tip: string }[];
  behavioral_stories: string[];
  technical_topics: string[];
  company_research: string[];
  created_at: string;
}

interface Stats {
  total_preps: number;
  unique_companies: number;
  total_questions: number;
  avg_questions_per_prep: number;
}

export default function InterviewPrepView() {
  const [preps, setPreps] = useState<Prep[]>([]);
  const [stats, setStats] = useState<Stats | null>(null);
  const [loading, setLoading] = useState(true);
  const [showGenForm, setShowGenForm] = useState(false);
  const [genForm, setGenForm] = useState({ job_id: '', role: '', company: '', difficulty: 'medium' });
  const [selectedPrep, setSelectedPrep] = useState<Prep | null>(null);
  const [roleQuestions, setRoleQuestions] = useState<any[]>([]);
  const [roleSearch, setRoleSearch] = useState('');

  const load = () => {
    Promise.all([
      interviewApi.getPreps().then(r => setPreps(r.data.preps ?? r.data ?? [])).catch(() => {}),
      interviewApi.getStats().then(r => setStats(r.data)).catch(() => {}),
    ]).finally(() => setLoading(false));
  };

  useEffect(() => { load(); }, []);

  const generatePrep = () => {
    if (!genForm.role.trim() && !genForm.job_id.trim()) return;
    interviewApi.generatePrep(genForm)
      .then(() => { setShowGenForm(false); setGenForm({ job_id: '', role: '', company: '', difficulty: 'medium' }); load(); })
      .catch(() => {});
  };

  const searchRoleQuestions = () => {
    if (!roleSearch.trim()) return;
    interviewApi.predictQuestions(roleSearch)
      .then(r => setRoleQuestions(r.data.questions ?? r.data ?? []))
      .catch(() => setRoleQuestions([]));
  };

  const loadPrepDetails = (id: string) => {
    if (selectedPrep?.id === id) { setSelectedPrep(null); return; }
    interviewApi.getPrep(id)
      .then(r => setSelectedPrep(r.data))
      .catch(() => {});
  };

  if (loading) return <LoadingSpinner text="Loading interview preparations..." />;

  const difficultyColors: Record<string, 'green' | 'gold' | 'red'> = { easy: 'green', medium: 'gold', hard: 'red' };

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="page-title">Interview AI</h1>
          <p className="text-gray-400 text-sm mt-1">AI-generated preparation, questions & company research</p>
        </div>
        <button onClick={() => setShowGenForm(!showGenForm)} className="btn-primary">
          + Generate Prep
        </button>
      </div>

      {/* Stats */}
      {stats && (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <StatCard label="Total Preps" value={stats.total_preps} icon="📋" />
          <StatCard label="Companies" value={stats.unique_companies} icon="🏢" />
          <StatCard label="Questions Generated" value={stats.total_questions} icon="❓" />
          <StatCard label="Avg Questions/Prep" value={stats.avg_questions_per_prep} icon="📊" />
        </div>
      )}

      {/* Generate Form */}
      {showGenForm && (
        <div className="card p-6 space-y-4">
          <h3 className="text-white font-medium">Generate Interview Prep</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <input type="text" value={genForm.role} onChange={e => setGenForm({...genForm, role: e.target.value})} placeholder="Role (e.g. Senior Backend Engineer)" className="input-field" />
            <input type="text" value={genForm.company} onChange={e => setGenForm({...genForm, company: e.target.value})} placeholder="Company name" className="input-field" />
            <input type="text" value={genForm.job_id} onChange={e => setGenForm({...genForm, job_id: e.target.value})} placeholder="Job ID (optional)" className="input-field" />
            <select value={genForm.difficulty} onChange={e => setGenForm({...genForm, difficulty: e.target.value})} className="input-field">
              <option value="easy">Easy</option>
              <option value="medium">Medium</option>
              <option value="hard">Hard</option>
            </select>
          </div>
          <div className="flex gap-3">
            <button onClick={generatePrep} className="btn-primary">Generate</button>
            <button onClick={() => setShowGenForm(false)} className="px-4 py-2 text-sm text-gray-400 hover:text-gray-200 transition-colors">Cancel</button>
          </div>
        </div>
      )}

      {/* Role Question Search */}
      <div className="card p-4">
        <div className="flex gap-3">
          <input
            type="text"
            value={roleSearch}
            onChange={e => setRoleSearch(e.target.value)}
            onKeyDown={e => e.key === 'Enter' && searchRoleQuestions()}
            placeholder="Search questions by role (e.g. Frontend Developer)..."
            className="input-field flex-1"
          />
          <button onClick={searchRoleQuestions} className="btn-primary px-6">Search</button>
        </div>
        {roleQuestions.length > 0 && (
          <div className="mt-4 space-y-2">
            {roleQuestions.map((q: any, i: number) => (
              <div key={i} className="p-3 bg-navy-800/50 rounded-lg">
                <div className="flex items-center gap-2 mb-1">
                  <Badge variant={difficultyColors[q.difficulty] ?? 'gold'}>{q.difficulty ?? 'medium'}</Badge>
                  <span className="text-xs text-gray-500">{q.category}</span>
                </div>
                <p className="text-sm text-white">{q.question}</p>
                {q.tip && <p className="text-xs text-gray-400 mt-1">💡 {q.tip}</p>}
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Prep List */}
      <div className="space-y-3">
        {preps.length === 0 ? (
          <EmptyState title="No interview preps" description="Generate your first interview prep to get started" />
        ) : (
          preps.map(prep => (
            <div key={prep.id} className="card p-4 cursor-pointer hover:border-cyan-400/30 transition-all" onClick={() => loadPrepDetails(prep.id)}>
              <div className="flex items-center justify-between">
                <div>
                  <div className="flex items-center gap-2">
                    <h3 className="text-white font-medium">{prep.job_title ?? prep.company_name}</h3>
                    <Badge variant={difficultyColors[prep.difficulty_level] ?? 'gold'}>{prep.difficulty_level}</Badge>
                  </div>
                  <p className="text-gray-400 text-sm mt-0.5">{prep.company_name} · {prep.questions?.length ?? 0} questions</p>
                </div>
                <span className="text-xs text-gray-500">{new Date(prep.created_at).toLocaleDateString()}</span>
              </div>
              {selectedPrep?.id === prep.id && (
                <div className="mt-4 space-y-4">
                  {/* Questions */}
                  {selectedPrep.questions?.length > 0 && (
                    <div>
                      <h4 className="text-xs text-gray-500 uppercase tracking-wide mb-2">Questions</h4>
                      <div className="space-y-2">
                        {selectedPrep.questions.map((q, i) => (
                          <div key={i} className="p-3 bg-navy-800/50 rounded-lg">
                            <p className="text-sm text-white">{q.question}</p>
                            {q.tip && <p className="text-xs text-cyan-400 mt-1">💡 {q.tip}</p>}
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                  {/* Behavioral Stories */}
                  {selectedPrep.behavioral_stories?.length > 0 && (
                    <div>
                      <h4 className="text-xs text-gray-500 uppercase tracking-wide mb-2">Behavioral Stories</h4>
                      <div className="space-y-1">
                        {selectedPrep.behavioral_stories.map((s, i) => (
                          <div key={i} className="flex items-start gap-2 text-sm text-gray-300">
                            <span className="text-purple-400 mt-0.5">•</span> {s}
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                  {/* Technical Topics */}
                  {selectedPrep.technical_topics?.length > 0 && (
                    <div>
                      <h4 className="text-xs text-gray-500 uppercase tracking-wide mb-2">Technical Topics</h4>
                      <div className="flex gap-2 flex-wrap">
                        {selectedPrep.technical_topics.map((t, i) => (
                          <span key={i} className="text-xs px-2 py-0.5 rounded-full bg-cyan-400/10 text-cyan-400">{t}</span>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              )}
            </div>
          ))
        )}
      </div>
    </div>
  );
}
