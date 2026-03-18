'use client';

import { useState } from 'react';
import { resumeApi } from '@/lib/api';
import { useAuthStore } from '@/lib/store';
import { LoadingSpinner } from '@/components/ui';

interface GeneratedResume {
  resume_content: string;
  cover_letter: string;
  outreach_email: string;
}

export default function ResumeManager() {
  const { user } = useAuthStore();
  const [jobTitle, setJobTitle] = useState('');
  const [companyName, setCompanyName] = useState('');
  const [jobDescription, setJobDescription] = useState('');
  const [result, setResult] = useState<GeneratedResume | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [activeTab, setActiveTab] = useState<'resume' | 'cover' | 'email'>('resume');

  const handleGenerate = async () => {
    if (!user || !jobTitle) return;
    setLoading(true);
    setError('');
    setResult(null);
    try {
      const res = await resumeApi.generate({
        user_id: user.id,
        job_id: '00000000-0000-0000-0000-000000000000',
        job_title: jobTitle,
        company_name: companyName,
        job_description: jobDescription,
        technologies: [],
        user_name: user.fullName,
      });
      setResult(res.data);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Generation failed');
    } finally {
      setLoading(false);
    }
  };

  const tabs = [
    { id: 'resume' as const, label: 'Resume', icon: '📄' },
    { id: 'cover' as const, label: 'Cover Letter', icon: '✉️' },
    { id: 'email' as const, label: 'Outreach Email', icon: '📨' },
  ];

  return (
    <div className="space-y-6 animate-fade-in">
      <div>
        <h1 className="page-title">Resume Manager</h1>
        <p className="text-gray-400 text-sm mt-1">AI-powered resume &amp; cover letter generation</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Input Form */}
        <div className="card p-6">
          <h2 className="section-title mb-4">
            <span className="gradient-text">Generate Tailored Content</span>
          </h2>
          <div className="space-y-4">
            <div>
              <label className="block text-xs text-gray-400 mb-1.5 uppercase tracking-wider">Job Title *</label>
              <input
                type="text"
                value={jobTitle}
                onChange={(e) => setJobTitle(e.target.value)}
                placeholder="e.g. Senior .NET Developer"
                className="input-field"
              />
            </div>
            <div>
              <label className="block text-xs text-gray-400 mb-1.5 uppercase tracking-wider">Company Name</label>
              <input
                type="text"
                value={companyName}
                onChange={(e) => setCompanyName(e.target.value)}
                className="input-field"
              />
            </div>
            <div>
              <label className="block text-xs text-gray-400 mb-1.5 uppercase tracking-wider">Job Description</label>
              <textarea
                value={jobDescription}
                onChange={(e) => setJobDescription(e.target.value)}
                rows={6}
                className="input-field resize-none"
                placeholder="Paste the full job description here..."
              />
            </div>
            <button
              onClick={handleGenerate}
              disabled={loading || !jobTitle}
              className="btn-primary w-full disabled:opacity-50"
            >
              {loading ? (
                <span className="flex items-center justify-center gap-2">
                  <svg className="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                  </svg>
                  Generating...
                </span>
              ) : (
                '✨ Generate Resume & Cover Letter'
              )}
            </button>
            {error && (
              <div className="p-3 rounded-xl bg-red-400/5 border border-red-400/10">
                <p className="text-red-400 text-sm">{error}</p>
              </div>
            )}
          </div>
        </div>

        {/* Output Preview */}
        <div className="card p-6">
          {/* Tab buttons */}
          <div className="flex gap-1 mb-4 p-1 bg-navy-950 rounded-xl">
            {tabs.map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`flex-1 flex items-center justify-center gap-1.5 px-3 py-2 rounded-lg text-sm font-medium transition-all ${
                  activeTab === tab.id
                    ? 'bg-surface text-cyan-400 shadow-glow'
                    : 'text-gray-500 hover:text-gray-300'
                }`}
              >
                <span>{tab.icon}</span>
                {tab.label}
              </button>
            ))}
          </div>

          {result ? (
            <div className="bg-navy-950 rounded-xl p-5 max-h-[500px] overflow-auto border border-gray-700/30">
              <pre className="text-gray-300 text-sm whitespace-pre-wrap font-mono leading-relaxed">
                {activeTab === 'resume' ? result.resume_content :
                 activeTab === 'cover' ? result.cover_letter :
                 result.outreach_email}
              </pre>
            </div>
          ) : (
            <div className="flex flex-col items-center justify-center py-16 text-center">
              <div className="w-16 h-16 rounded-2xl bg-cyan-400/5 flex items-center justify-center mb-4">
                <svg className="w-8 h-8 text-cyan-400/40" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                </svg>
              </div>
              <p className="text-gray-500 text-sm">Generated content will appear here</p>
              <p className="text-gray-600 text-xs mt-1">Fill in the job details and click generate</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
