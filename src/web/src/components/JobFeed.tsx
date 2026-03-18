'use client';

import { useEffect, useState, useCallback } from 'react';
import { jobsApi, applicationsApi, feedbackApi, skillsApi } from '@/lib/api';
import { useAuthStore } from '@/lib/store';
import { MatchScore, Badge, SkillBadge, LoadingSpinner, EmptyState } from '@/components/ui';

interface Job {
  id: string;
  source: string;
  job_title: string;
  company_name: string | null;
  job_link: string;
  salary_or_rate: string | null;
  location: string | null;
  is_remote: boolean;
  contract_type: string | null;
  date_discovered: string | null;
  analysis?: {
    match_score: number;
    technologies: string[];
    ai_summary: string | null;
    embedding_id?: string | null;
    role_category?: string | null;
    visa_sponsorship?: boolean | null;
    experience_years_min?: number | null;
    experience_years_max?: number | null;
    matched_skills?: string[] | null;
    missing_skills?: string[] | null;
    match_reasons?: string[] | null;
  } | null;
}

interface Filters {
  keyword: string;
  source: string;
  sources: string[];
  remoteOnly: boolean;
  minScore: number;
  maxScore: number;
  contractOnly: boolean;
  technologies: string[];
  locations: string[];
  companies: string[];
  seniority: string[];
  sort_by: string;
  sort_order: string;
  roleCategories: string[];
  skills: string[];
  visaSponsorship: boolean;
  experienceMin: number;
  experienceMax: number;
}

interface FilterOptions {
  sources: string[];
  technologies: string[] | { name: string; count: number }[];
  locations: string[];
  companies: string[];
  contract_types: string[];
  seniority_levels: string[];
  role_categories?: { id: string; label: string; count?: number }[];
  skill_categories?: Record<string, string[]>;
}

export default function JobFeed() {
  const { user } = useAuthStore();
  const [jobs, setJobs] = useState<Job[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(true);
  const [applying, setApplying] = useState<string | null>(null);
  const [showFilters, setShowFilters] = useState(false);
  const [selectedJob, setSelectedJob] = useState<Job | null>(null);
  const [filterOptions, setFilterOptions] = useState<FilterOptions | null>(null);
  const [semanticQuery, setSemanticQuery] = useState('');
  const [searchMode, setSearchMode] = useState<'standard' | 'semantic'>('standard');
  const [filters, setFilters] = useState<Filters>({
    keyword: '',
    source: '',
    sources: [],
    remoteOnly: false,
    minScore: 0,
    maxScore: 100,
    contractOnly: false,
    technologies: [],
    locations: [],
    companies: [],
    seniority: [],
    sort_by: 'date_discovered',
    sort_order: 'desc',
    roleCategories: [],
    skills: [],
    visaSponsorship: false,
    experienceMin: 0,
    experienceMax: 0,
  });
  const [skillTaxonomy, setSkillTaxonomy] = useState<Record<string, string[]>>({});
  const [skillSearch, setSkillSearch] = useState('');

  useEffect(() => {
    jobsApi.getFilterOptions?.().then(r => setFilterOptions(r.data)).catch(() => {});
    skillsApi.getTaxonomy?.().then(r => {
      if (r.data?.skill_categories) setSkillTaxonomy(r.data.skill_categories);
    }).catch(() => {});
  }, []);

  const fetchJobs = useCallback(async () => {
    setLoading(true);
    try {
      if (searchMode === 'semantic' && semanticQuery) {
        const res = await jobsApi.semanticSearch(semanticQuery, filters.technologies.length > 0 ? filters.technologies : undefined);
        setJobs(res.data?.results ?? []);
        setTotal(res.data?.results?.length ?? 0);
      } else {
        const res = await jobsApi.getJobs({
          page,
          pageSize: 20,
          source: filters.source || undefined,
          sources: filters.sources.length > 0 ? filters.sources : undefined,
          remote_only: filters.remoteOnly || undefined,
          min_score: filters.minScore > 0 ? filters.minScore : undefined,
          max_score: filters.maxScore < 100 ? filters.maxScore : undefined,
          search: filters.keyword || undefined,
          technologies: filters.technologies.length > 0 ? filters.technologies : undefined,
          locations: filters.locations.length > 0 ? filters.locations : undefined,
          companies: filters.companies.length > 0 ? filters.companies : undefined,
          seniority: filters.seniority.length > 0 ? filters.seniority : undefined,
          role_categories: filters.roleCategories.length > 0 ? filters.roleCategories : undefined,
          skills: filters.skills.length > 0 ? filters.skills : undefined,
          visa_sponsorship: filters.visaSponsorship || undefined,
          experience_min: filters.experienceMin > 0 ? filters.experienceMin : undefined,
          experience_max: filters.experienceMax > 0 ? filters.experienceMax : undefined,
          sort_by: filters.sort_by,
          sort_order: filters.sort_order,
        });
        setJobs(res.data?.data ?? []);
        setTotal(res.data?.total ?? 0);
      }
    } catch {
      setJobs([]);
    } finally {
      setLoading(false);
    }
  }, [page, filters, searchMode, semanticQuery]);

  useEffect(() => { fetchJobs(); }, [fetchJobs]);

  const handleApply = async (jobId: string) => {
    if (!user) return;
    setApplying(jobId);
    try {
      await applicationsApi.apply(jobId);
    } catch {
      // silent
    } finally {
      setApplying(null);
    }
  };

  const handleFeedback = async (jobId: string, type: string) => {
    try {
      await feedbackApi.submitJobFeedback(jobId, type);
    } catch {
      // silent
    }
  };

  const totalPages = Math.ceil(total / 20);
  const sources = filterOptions?.sources ?? ['RemoteOK', 'WeWorkRemotely', 'LinkedIn', 'Indeed', 'Dice'];

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="page-title">Job Feed</h1>
          <p className="text-gray-400 text-sm mt-1">{total} jobs discovered</p>
        </div>
        <div className="flex items-center gap-3">
          {/* Search Mode Toggle */}
          <div className="flex items-center bg-navy-800 rounded-xl overflow-hidden border border-gray-700/30">
            <button onClick={() => setSearchMode('standard')}
              className={`px-3 py-1.5 text-xs font-medium transition-all ${searchMode === 'standard' ? 'bg-cyan-400/10 text-cyan-400' : 'text-gray-400'}`}>
              Standard
            </button>
            <button onClick={() => setSearchMode('semantic')}
              className={`px-3 py-1.5 text-xs font-medium transition-all ${searchMode === 'semantic' ? 'bg-purple-400/10 text-purple-400' : 'text-gray-400'}`}>
              🧠 Semantic
            </button>
          </div>
          <button
            onClick={() => setShowFilters(!showFilters)}
            className={`btn-secondary flex items-center gap-2 text-sm ${showFilters ? 'border-cyan-400/40 text-cyan-400' : ''}`}
          >
            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M3 4a1 1 0 011-1h16a1 1 0 011 1v2.586a1 1 0 01-.293.707l-6.414 6.414a1 1 0 00-.293.707V17l-4 4v-6.586a1 1 0 00-.293-.707L3.293 7.293A1 1 0 013 6.586V4z" />
            </svg>
            Filters
            {(filters.remoteOnly || filters.contractOnly || filters.minScore > 0 || filters.technologies.length > 0 || filters.roleCategories.length > 0 || filters.skills.length > 0 || filters.visaSponsorship) && (
              <span className="w-2 h-2 rounded-full bg-cyan-400" />
            )}
          </button>
          <button onClick={fetchJobs} className="btn-primary text-sm">
            <svg className="w-4 h-4 inline mr-1" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
            </svg>
            Refresh
          </button>
        </div>
      </div>

      {/* Semantic Search Bar */}
      {searchMode === 'semantic' && (
        <div className="card p-4 animate-slide-up border-purple-400/20">
          <div className="flex items-center gap-3">
            <span className="text-xl">🧠</span>
            <input
              type="text"
              value={semanticQuery}
              onChange={(e) => setSemanticQuery(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && fetchJobs()}
              placeholder="Describe your ideal job in natural language... e.g. 'Senior React developer working on AI products, remote friendly'"
              className="input-field text-sm flex-1"
            />
            <button onClick={fetchJobs} className="btn-primary text-sm whitespace-nowrap">Search</button>
          </div>
          <p className="text-xs text-gray-500 mt-2 ml-9">AI-powered vector search across all analyzed jobs</p>
        </div>
      )}

      {/* Filter Panel */}
      {showFilters && (
        <div className="card p-6 animate-slide-up">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            {/* Keyword Search */}
            <div>
              <label className="block text-xs text-gray-400 mb-1.5 uppercase tracking-wider">Keyword</label>
              <input
                type="text"
                value={filters.keyword}
                onChange={(e) => setFilters(f => ({ ...f, keyword: e.target.value }))}
                placeholder="Job title, company, tech..."
                className="input-field text-sm"
              />
            </div>

            {/* Source Filter */}
            <div>
              <label className="block text-xs text-gray-400 mb-1.5 uppercase tracking-wider">Source</label>
              <select
                value={filters.source}
                onChange={(e) => { setFilters(f => ({ ...f, source: e.target.value })); setPage(1); }}
                className="input-field text-sm"
              >
                <option value="">All Sources</option>
                {sources.map(s => <option key={s} value={s}>{s}</option>)}
              </select>
            </div>

            {/* Min Match Score */}
            <div>
              <label className="block text-xs text-gray-400 mb-1.5 uppercase tracking-wider">
                Min Score: <span className="text-cyan-400">{filters.minScore}</span>
              </label>
              <input
                type="range"
                min={0}
                max={100}
                step={5}
                value={filters.minScore}
                onChange={(e) => setFilters(f => ({ ...f, minScore: parseInt(e.target.value) }))}
                className="w-full accent-cyan-400"
              />
            </div>

            {/* Toggles */}
            <div className="flex flex-col gap-3 justify-center">
              <label className="flex items-center gap-2 cursor-pointer">
                <div className={`w-9 h-5 rounded-full transition-colors relative ${filters.remoteOnly ? 'bg-cyan-400' : 'bg-navy-700'}`}
                  onClick={() => setFilters(f => ({ ...f, remoteOnly: !f.remoteOnly }))}>
                  <div className={`absolute w-4 h-4 rounded-full bg-white top-0.5 transition-transform ${filters.remoteOnly ? 'translate-x-4' : 'translate-x-0.5'}`} />
                </div>
                <span className="text-sm text-gray-300">Remote Only</span>
              </label>
              <label className="flex items-center gap-2 cursor-pointer">
                <div className={`w-9 h-5 rounded-full transition-colors relative ${filters.contractOnly ? 'bg-gold-400' : 'bg-navy-700'}`}
                  onClick={() => setFilters(f => ({ ...f, contractOnly: !f.contractOnly }))}>
                  <div className={`absolute w-4 h-4 rounded-full bg-white top-0.5 transition-transform ${filters.contractOnly ? 'translate-x-4' : 'translate-x-0.5'}`} />
                </div>
                <span className="text-sm text-gray-300">Contract Only</span>
              </label>
            </div>
          </div>

          {/* Sort Controls */}
          <div className="flex items-center gap-4 mt-4 pt-4 border-t border-gray-700/20">
            <label className="text-xs text-gray-400 uppercase tracking-wider">Sort by</label>
            <select value={filters.sort_by} onChange={(e) => setFilters(f => ({ ...f, sort_by: e.target.value }))} className="input-field text-sm w-auto">
              <option value="date_discovered">Date Discovered</option>
              <option value="match_score">Match Score</option>
              <option value="company_name">Company</option>
              <option value="job_title">Title</option>
            </select>
            <button onClick={() => setFilters(f => ({ ...f, sort_order: f.sort_order === 'desc' ? 'asc' : 'desc' }))}
              className="btn-secondary text-xs">
              {filters.sort_order === 'desc' ? '↓ Desc' : '↑ Asc'}
            </button>
          </div>

          {/* Technology Multi-Select */}
          {filterOptions && filterOptions.technologies.length > 0 && (
            <div className="mt-4 pt-4 border-t border-gray-700/20">
              <label className="block text-xs text-gray-400 mb-2 uppercase tracking-wider">Technologies</label>
              <div className="flex flex-wrap gap-1.5">
                {(filterOptions.technologies as any[]).slice(0, 30).map(tech => {
                  const name = typeof tech === 'string' ? tech : tech.name;
                  const count = typeof tech === 'object' ? tech.count : null;
                  return (
                    <button key={name}
                      onClick={() => setFilters(f => ({
                        ...f,
                        technologies: f.technologies.includes(name)
                          ? f.technologies.filter(t => t !== name)
                          : [...f.technologies, name],
                      }))}
                      className={`px-2.5 py-1 rounded-lg text-xs font-medium transition-all ${
                        filters.technologies.includes(name)
                          ? 'bg-cyan-400/15 text-cyan-400 border border-cyan-400/30'
                          : 'bg-navy-800 text-gray-400 border border-gray-700/30 hover:border-gray-600/50'
                      }`}>
                      {name}{count ? ` (${count})` : ''}
                    </button>
                  );
                })}
              </div>
            </div>
          )}

          {/* Role Category Filter */}
          {filterOptions?.role_categories && filterOptions.role_categories.length > 0 && (
            <div className="mt-4 pt-4 border-t border-gray-700/20">
              <label className="block text-xs text-gray-400 mb-2 uppercase tracking-wider">Role Category</label>
              <div className="flex flex-wrap gap-1.5">
                {filterOptions.role_categories.map(rc => (
                  <button key={rc.id}
                    onClick={() => setFilters(f => ({
                      ...f,
                      roleCategories: f.roleCategories.includes(rc.id)
                        ? f.roleCategories.filter(r => r !== rc.id)
                        : [...f.roleCategories, rc.id],
                    }))}
                    className={`px-2.5 py-1 rounded-lg text-xs font-medium transition-all ${
                      filters.roleCategories.includes(rc.id)
                        ? 'bg-purple-400/15 text-purple-400 border border-purple-400/30'
                        : 'bg-navy-800 text-gray-400 border border-gray-700/30 hover:border-gray-600/50'
                    }`}>
                    {rc.label}
                  </button>
                ))}
              </div>
            </div>
          )}

          {/* Skill Multi-Select */}
          {Object.keys(skillTaxonomy).length > 0 && (
            <div className="mt-4 pt-4 border-t border-gray-700/20">
              <div className="flex items-center justify-between mb-2">
                <label className="block text-xs text-gray-400 uppercase tracking-wider">Skills Filter</label>
                {filters.skills.length > 0 && (
                  <button onClick={() => setFilters(f => ({ ...f, skills: [] }))}
                    className="text-xs text-red-400 hover:text-red-300">Clear ({filters.skills.length})</button>
                )}
              </div>
              <input
                type="text"
                value={skillSearch}
                onChange={(e) => setSkillSearch(e.target.value)}
                placeholder="Search skills..."
                className="input-field text-sm mb-2"
              />
              <div className="max-h-48 overflow-y-auto space-y-3">
                {Object.entries(skillTaxonomy).map(([category, skills]) => {
                  const filtered = skills.filter(s =>
                    !skillSearch || s.toLowerCase().includes(skillSearch.toLowerCase())
                  );
                  if (filtered.length === 0) return null;
                  return (
                    <div key={category}>
                      <p className="text-[10px] text-gray-500 uppercase tracking-wider mb-1">{category.replace(/_/g, ' ')}</p>
                      <div className="flex flex-wrap gap-1">
                        {filtered.slice(0, 15).map(skill => (
                          <button key={skill}
                            onClick={() => setFilters(f => ({
                              ...f,
                              skills: f.skills.includes(skill)
                                ? f.skills.filter(s => s !== skill)
                                : [...f.skills, skill],
                            }))}
                            className={`px-2 py-0.5 rounded text-[11px] font-medium transition-all ${
                              filters.skills.includes(skill)
                                ? 'bg-green-400/15 text-green-400 border border-green-400/30'
                                : 'bg-navy-800/50 text-gray-500 border border-gray-700/20 hover:border-gray-600/50'
                            }`}>
                            {skill}
                          </button>
                        ))}
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          )}

          {/* Visa & Experience Filters */}
          <div className="mt-4 pt-4 border-t border-gray-700/20 grid grid-cols-1 md:grid-cols-3 gap-4">
            <label className="flex items-center gap-2 cursor-pointer">
              <div className={`w-9 h-5 rounded-full transition-colors relative ${filters.visaSponsorship ? 'bg-green-400' : 'bg-navy-700'}`}
                onClick={() => setFilters(f => ({ ...f, visaSponsorship: !f.visaSponsorship }))}>
                <div className={`absolute w-4 h-4 rounded-full bg-white top-0.5 transition-transform ${filters.visaSponsorship ? 'translate-x-4' : 'translate-x-0.5'}`} />
              </div>
              <span className="text-sm text-gray-300">Visa Sponsorship</span>
            </label>
            <div>
              <label className="block text-xs text-gray-400 mb-1 uppercase tracking-wider">Min Experience</label>
              <input type="number" min={0} max={20} value={filters.experienceMin || ''}
                onChange={(e) => setFilters(f => ({ ...f, experienceMin: parseInt(e.target.value) || 0 }))}
                placeholder="0" className="input-field text-sm" />
            </div>
            <div>
              <label className="block text-xs text-gray-400 mb-1 uppercase tracking-wider">Max Experience</label>
              <input type="number" min={0} max={30} value={filters.experienceMax || ''}
                onChange={(e) => setFilters(f => ({ ...f, experienceMax: parseInt(e.target.value) || 0 }))}
                placeholder="Any" className="input-field text-sm" />
            </div>
          </div>
        </div>
      )}

      {/* Source Pills */}
      <div className="flex gap-2 flex-wrap">
        {sources.map((s) => (
          <button
            key={s}
            onClick={() => { setFilters(f => ({ ...f, source: s })); setPage(1); }}
            className={`px-3 py-1.5 rounded-xl text-xs font-medium transition-all ${
              filters.source === s
                ? 'bg-cyan-400/10 text-cyan-400 border border-cyan-400/30 shadow-glow'
                : 'bg-surface text-gray-400 border border-transparent hover:border-gray-700/50'
            }`}
          >
            {s || 'All'}
          </button>
        ))}
      </div>

      {/* Job List */}
      {loading ? (
        <LoadingSpinner text="Discovering jobs..." />
      ) : jobs.length === 0 ? (
        <EmptyState
          icon="🔍"
          title="No jobs found"
          description="Try adjusting your filters or wait for crawlers to discover new jobs automatically."
        />
      ) : (
        <div className="space-y-3">
          {jobs.map((job, i) => (
            <div
              key={job.id}
              className="card-hover p-5 cursor-pointer animate-slide-up"
              style={{ animationDelay: `${i * 30}ms` }}
              onClick={() => setSelectedJob(selectedJob?.id === job.id ? null : job)}
            >
              <div className="flex items-start gap-4">
                {/* Match Score */}
                <MatchScore score={job.analysis?.match_score ?? 0} size="md" />

                {/* Job Info */}
                <div className="flex-1 min-w-0">
                  <div className="flex items-start justify-between gap-3">
                    <div>
                      <h3 className="text-base font-semibold text-white group-hover:text-cyan-400 transition-colors">
                        {job.job_title}
                      </h3>
                      <p className="text-sm text-gray-400 mt-0.5">
                        {job.company_name || 'Unknown Company'} · {job.location || 'Remote'} · {job.source}
                      </p>
                    </div>
                    {job.salary_or_rate && (
                      <span className="text-sm font-semibold text-green-400 whitespace-nowrap">{job.salary_or_rate}</span>
                    )}
                  </div>

                  {/* Tags */}
                  <div className="flex flex-wrap items-center gap-2 mt-2">
                    {job.is_remote && <Badge variant="cyan" dot>Remote</Badge>}
                    {job.contract_type && <Badge variant="gold">{job.contract_type}</Badge>}
                    {job.analysis?.role_category && (
                      <Badge variant="gray">{job.analysis.role_category.replace(/_/g, ' ')}</Badge>
                    )}
                    {job.analysis?.visa_sponsorship && (
                      <span className="px-2 py-0.5 rounded text-[10px] font-medium bg-green-400/10 text-green-400 border border-green-400/20">Visa</span>
                    )}
                    {job.analysis?.experience_years_min != null && (
                      <span className="text-[10px] text-gray-500">
                        {job.analysis.experience_years_min}–{job.analysis.experience_years_max ?? '?'}yr exp
                      </span>
                    )}
                    {job.date_discovered && (
                      <Badge variant="gray">{new Date(job.date_discovered).toLocaleDateString()}</Badge>
                    )}
                  </div>

                  {/* Matched & Missing Skills */}
                  {job.analysis?.matched_skills && job.analysis.matched_skills.length > 0 && (
                    <div className="flex flex-wrap gap-1 mt-2">
                      {job.analysis.matched_skills.slice(0, 6).map(s => (
                        <span key={s} className="px-1.5 py-0.5 rounded text-[10px] font-medium bg-green-400/10 text-green-400 border border-green-400/20">{s}</span>
                      ))}
                      {(job.analysis.missing_skills?.length ?? 0) > 0 && job.analysis.missing_skills!.slice(0, 3).map(s => (
                        <span key={s} className="px-1.5 py-0.5 rounded text-[10px] font-medium bg-red-400/10 text-red-400 border border-red-400/20 line-through">{s}</span>
                      ))}
                    </div>
                  )}

                  {/* Tech Stack */}
                  {job.analysis?.technologies && job.analysis.technologies.length > 0 && (
                    <div className="flex flex-wrap gap-1.5 mt-3">
                      {job.analysis.technologies.slice(0, 8).map((tech) => (
                        <SkillBadge key={tech} name={tech} matched />
                      ))}
                      {job.analysis.technologies.length > 8 && (
                        <span className="text-xs text-gray-500 self-center">+{job.analysis.technologies.length - 8} more</span>
                      )}
                    </div>
                  )}

                  {/* AI Summary (expanded) */}
                  {selectedJob?.id === job.id && (
                    <div className="mt-3 space-y-2 animate-slide-up">
                      {job.analysis?.ai_summary && (
                        <div className="p-3 rounded-xl bg-navy-950 border border-gray-700/30">
                          <p className="text-xs text-gray-400 uppercase tracking-wider mb-1">AI Analysis</p>
                          <p className="text-sm text-gray-300">{job.analysis.ai_summary}</p>
                        </div>
                      )}
                      {job.analysis?.match_reasons && job.analysis.match_reasons.length > 0 && (
                        <div className="p-3 rounded-xl bg-navy-950 border border-cyan-400/10">
                          <p className="text-xs text-cyan-400 uppercase tracking-wider mb-1">Why This Matches</p>
                          <ul className="text-sm text-gray-300 space-y-0.5">
                            {job.analysis.match_reasons.map((reason, i) => (
                              <li key={i} className="flex items-start gap-1.5">
                                <span className="text-cyan-400 mt-0.5">•</span> {reason}
                              </li>
                            ))}
                          </ul>
                        </div>
                      )}
                    </div>
                  )}
                </div>

                {/* Actions */}
                <div className="flex flex-col gap-2 flex-shrink-0">
                  <a
                    href={job.job_link}
                    target="_blank"
                    rel="noopener noreferrer"
                    onClick={(e) => e.stopPropagation()}
                    className="btn-secondary text-xs text-center"
                  >
                    View
                  </a>
                  <button
                    onClick={(e) => { e.stopPropagation(); handleApply(job.id); }}
                    disabled={applying === job.id}
                    className="btn-primary text-xs disabled:opacity-50"
                  >
                    {applying === job.id ? '...' : 'Apply'}
                  </button>
                  <div className="flex gap-1">
                    <button
                      onClick={(e) => { e.stopPropagation(); handleFeedback(job.id, 'thumbs_up'); }}
                      className="flex-1 text-xs py-1 rounded-lg bg-green-400/5 text-green-400 hover:bg-green-400/15 transition-all"
                      title="Great match"
                    >👍</button>
                    <button
                      onClick={(e) => { e.stopPropagation(); handleFeedback(job.id, 'thumbs_down'); }}
                      className="flex-1 text-xs py-1 rounded-lg bg-red-400/5 text-red-400 hover:bg-red-400/15 transition-all"
                      title="Not relevant"
                    >👎</button>
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Pagination */}
      {totalPages > 1 && (
        <div className="flex items-center justify-center gap-3 pt-4">
          <button
            onClick={() => setPage(Math.max(1, page - 1))}
            disabled={page === 1}
            className="btn-secondary text-sm disabled:opacity-30"
          >
            ← Prev
          </button>
          <div className="flex items-center gap-1">
            {Array.from({ length: Math.min(5, totalPages) }, (_, i) => {
              const p = page <= 3 ? i + 1 : page - 2 + i;
              if (p > totalPages) return null;
              return (
                <button
                  key={p}
                  onClick={() => setPage(p)}
                  className={`w-8 h-8 rounded-lg text-sm font-medium transition-all ${
                    p === page
                      ? 'bg-cyan-400/10 text-cyan-400 border border-cyan-400/30'
                      : 'text-gray-400 hover:bg-surface-light'
                  }`}
                >
                  {p}
                </button>
              );
            })}
          </div>
          <button
            onClick={() => setPage(Math.min(totalPages, page + 1))}
            disabled={page === totalPages}
            className="btn-secondary text-sm disabled:opacity-30"
          >
            Next →
          </button>
        </div>
      )}
    </div>
  );
}
