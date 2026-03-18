'use client';

import { useEffect, useState, useCallback } from 'react';
import { profileApi, skillsApi } from '@/lib/api';
import { LoadingSpinner, EmptyState } from '@/components/ui';

interface RoleTemplate {
  id: string;
  label: string;
  search_queries: string[];
  core_skills: string[];
}

interface SavedSearch {
  id: string;
  name: string;
  role_categories: string[];
  skills_filter: string[];
  min_score_threshold: number;
  is_active: boolean;
  notify_on_match: boolean;
  match_count: number;
  last_run_at: string | null;
}

interface ProfilePreview {
  profile_text: string;
  search_queries: string[];
  preferred_roles: string[];
  skills: string[];
}

export default function SkillProfileSetup() {
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [roleTemplates, setRoleTemplates] = useState<RoleTemplate[]>([]);
  const [skillTaxonomy, setSkillTaxonomy] = useState<Record<string, string[]>>({});
  const [selectedRoles, setSelectedRoles] = useState<string[]>([]);
  const [selectedSkills, setSelectedSkills] = useState<string[]>([]);
  const [preferredLocations, setPreferredLocations] = useState<string[]>(['Remote', 'USA']);
  const [visaRequired, setVisaRequired] = useState(false);
  const [preview, setPreview] = useState<ProfilePreview | null>(null);
  const [savedSearches, setSavedSearches] = useState<SavedSearch[]>([]);
  const [skillSearch, setSkillSearch] = useState('');
  const [newSearchName, setNewSearchName] = useState('');
  const [activeTab, setActiveTab] = useState<'roles' | 'skills' | 'searches' | 'preview'>('roles');

  const fetchData = useCallback(async () => {
    setLoading(true);
    try {
      const [taxonomyRes, profileRes, searchesRes] = await Promise.all([
        skillsApi.getTaxonomy(),
        profileApi.getProfile(),
        skillsApi.getSavedSearches(),
      ]);

      if (taxonomyRes.data) {
        setSkillTaxonomy(taxonomyRes.data.skill_categories || {});
        setRoleTemplates(taxonomyRes.data.role_templates || []);
      }

      if (profileRes.data) {
        setSelectedRoles(profileRes.data.preferred_roles || []);
        setSelectedSkills(profileRes.data.preferred_technologies || []);
        setPreferredLocations(profileRes.data.preferred_locations || ['Remote', 'USA']);
        setVisaRequired(profileRes.data.visa_required || false);
      }

      setSavedSearches(searchesRes.data || []);
    } catch {
      // silent
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { fetchData(); }, [fetchData]);

  const handleSave = async () => {
    setSaving(true);
    try {
      await profileApi.updateProfile({
        preferred_roles: selectedRoles,
        preferred_technologies: selectedSkills,
        preferred_locations: preferredLocations,
        visa_required: visaRequired,
      });
      // Refresh preview
      const res = await skillsApi.getProfilePreview();
      setPreview(res.data);
      setActiveTab('preview');
    } catch {
      // silent
    } finally {
      setSaving(false);
    }
  };

  const handleCreateSearch = async () => {
    if (!newSearchName.trim()) return;
    try {
      await skillsApi.createSavedSearch({
        name: newSearchName,
        role_categories: selectedRoles,
        skills_filter: selectedSkills,
        min_score: 50,
        notify_on_match: true,
      });
      setNewSearchName('');
      const res = await skillsApi.getSavedSearches();
      setSavedSearches(res.data || []);
    } catch {
      // silent
    }
  };

  const handleDeleteSearch = async (id: string) => {
    try {
      await skillsApi.deleteSavedSearch(id);
      setSavedSearches(s => s.filter(x => x.id !== id));
    } catch {
      // silent
    }
  };

  const handleToggleSearch = async (id: string) => {
    try {
      await skillsApi.toggleSavedSearch(id);
      setSavedSearches(s => s.map(x => x.id === id ? { ...x, is_active: !x.is_active } : x));
    } catch {
      // silent
    }
  };

  const toggleRole = (roleId: string) => {
    setSelectedRoles(prev =>
      prev.includes(roleId) ? prev.filter(r => r !== roleId) : [...prev, roleId]
    );
  };

  const toggleSkill = (skill: string) => {
    setSelectedSkills(prev =>
      prev.includes(skill) ? prev.filter(s => s !== skill) : [...prev, skill]
    );
  };

  const addQuickSkills = (template: RoleTemplate) => {
    setSelectedSkills(prev => {
      const newSkills = template.core_skills.filter(s => !prev.includes(s));
      return [...prev, ...newSkills];
    });
  };

  if (loading) return <LoadingSpinner text="Loading skill profile..." />;

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="page-title">Skill Profile</h1>
          <p className="text-gray-400 text-sm mt-1">
            Configure your skills, preferred roles, and search preferences for AI-powered matching
          </p>
        </div>
        <button onClick={handleSave} disabled={saving} className="btn-primary text-sm disabled:opacity-50">
          {saving ? 'Saving...' : 'Save Profile'}
        </button>
      </div>

      {/* Stats Bar */}
      <div className="grid grid-cols-4 gap-4">
        <div className="card p-4 text-center">
          <p className="text-2xl font-bold text-cyan-400">{selectedRoles.length}</p>
          <p className="text-xs text-gray-500 mt-1">Roles Selected</p>
        </div>
        <div className="card p-4 text-center">
          <p className="text-2xl font-bold text-purple-400">{selectedSkills.length}</p>
          <p className="text-xs text-gray-500 mt-1">Skills Tagged</p>
        </div>
        <div className="card p-4 text-center">
          <p className="text-2xl font-bold text-green-400">{savedSearches.length}</p>
          <p className="text-xs text-gray-500 mt-1">Saved Searches</p>
        </div>
        <div className="card p-4 text-center">
          <p className="text-2xl font-bold text-gold-400">{savedSearches.filter(s => s.is_active).length}</p>
          <p className="text-xs text-gray-500 mt-1">Active Alerts</p>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex items-center gap-1 bg-navy-800 rounded-xl p-1 border border-gray-700/30">
        {(['roles', 'skills', 'searches', 'preview'] as const).map(tab => (
          <button key={tab}
            onClick={() => { if (tab === 'preview') skillsApi.getProfilePreview().then(r => setPreview(r.data)).catch(() => {}); setActiveTab(tab); }}
            className={`flex-1 px-4 py-2 rounded-lg text-sm font-medium transition-all ${
              activeTab === tab
                ? 'bg-cyan-400/10 text-cyan-400'
                : 'text-gray-400 hover:text-gray-200'
            }`}>
            {tab === 'roles' && '🎯 '}{tab === 'skills' && '⚡ '}{tab === 'searches' && '🔍 '}{tab === 'preview' && '👁 '}
            {tab.charAt(0).toUpperCase() + tab.slice(1)}
          </button>
        ))}
      </div>

      {/* Roles Tab */}
      {activeTab === 'roles' && (
        <div className="space-y-4 animate-slide-up">
          <p className="text-sm text-gray-400">Select the roles that match your expertise. The AI will optimize job searches and matching based on your selections.</p>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            {roleTemplates.map(template => {
              const isSelected = selectedRoles.includes(template.id);
              return (
                <div key={template.id}
                  onClick={() => toggleRole(template.id)}
                  className={`card p-4 cursor-pointer transition-all border-2 ${
                    isSelected
                      ? 'border-cyan-400/40 bg-cyan-400/5'
                      : 'border-transparent hover:border-gray-700/50'
                  }`}>
                  <div className="flex items-center justify-between">
                    <h3 className={`font-semibold ${isSelected ? 'text-cyan-400' : 'text-white'}`}>
                      {template.label}
                    </h3>
                    <div className={`w-5 h-5 rounded-full border-2 flex items-center justify-center transition-all ${
                      isSelected ? 'border-cyan-400 bg-cyan-400' : 'border-gray-600'
                    }`}>
                      {isSelected && (
                        <svg className="w-3 h-3 text-navy-900" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} d="M5 13l4 4L19 7" />
                        </svg>
                      )}
                    </div>
                  </div>
                  <div className="flex flex-wrap gap-1 mt-2">
                    {template.core_skills.slice(0, 6).map(skill => (
                      <span key={skill} className="px-2 py-0.5 rounded text-[10px] bg-navy-800/80 text-gray-400">
                        {skill}
                      </span>
                    ))}
                    {template.core_skills.length > 6 && (
                      <span className="text-[10px] text-gray-500">+{template.core_skills.length - 6}</span>
                    )}
                  </div>
                  {isSelected && (
                    <button
                      onClick={(e) => { e.stopPropagation(); addQuickSkills(template); }}
                      className="mt-2 text-xs text-cyan-400 hover:text-cyan-300"
                    >
                      + Add all core skills
                    </button>
                  )}
                </div>
              );
            })}
          </div>

          {/* Location & Visa */}
          <div className="card p-4 space-y-4">
            <h3 className="text-sm font-semibold text-white">Location Preferences</h3>
            <div className="flex flex-wrap gap-2">
              {['Remote', 'USA', 'Hybrid', 'On-site'].map(loc => (
                <button key={loc}
                  onClick={() => setPreferredLocations(prev =>
                    prev.includes(loc) ? prev.filter(l => l !== loc) : [...prev, loc]
                  )}
                  className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-all ${
                    preferredLocations.includes(loc)
                      ? 'bg-cyan-400/15 text-cyan-400 border border-cyan-400/30'
                      : 'bg-navy-800 text-gray-400 border border-gray-700/30'
                  }`}>
                  {loc}
                </button>
              ))}
            </div>
            <label className="flex items-center gap-2 cursor-pointer">
              <div className={`w-9 h-5 rounded-full transition-colors relative ${visaRequired ? 'bg-green-400' : 'bg-navy-700'}`}
                onClick={() => setVisaRequired(!visaRequired)}>
                <div className={`absolute w-4 h-4 rounded-full bg-white top-0.5 transition-transform ${visaRequired ? 'translate-x-4' : 'translate-x-0.5'}`} />
              </div>
              <span className="text-sm text-gray-300">I need visa sponsorship</span>
            </label>
          </div>
        </div>
      )}

      {/* Skills Tab */}
      {activeTab === 'skills' && (
        <div className="space-y-4 animate-slide-up">
          {/* Selected Skills */}
          {selectedSkills.length > 0 && (
            <div className="card p-4">
              <div className="flex items-center justify-between mb-2">
                <h3 className="text-sm font-semibold text-white">Your Skills ({selectedSkills.length})</h3>
                <button onClick={() => setSelectedSkills([])} className="text-xs text-red-400 hover:text-red-300">Clear All</button>
              </div>
              <div className="flex flex-wrap gap-1.5">
                {selectedSkills.map(skill => (
                  <button key={skill}
                    onClick={() => toggleSkill(skill)}
                    className="px-2.5 py-1 rounded-lg text-xs font-medium bg-cyan-400/15 text-cyan-400 border border-cyan-400/30 hover:bg-red-400/10 hover:border-red-400/30 hover:text-red-400 transition-all">
                    {skill} ×
                  </button>
                ))}
              </div>
            </div>
          )}

          {/* Skill Search */}
          <div className="card p-4">
            <input
              type="text"
              value={skillSearch}
              onChange={(e) => setSkillSearch(e.target.value)}
              placeholder="Search skills..."
              className="input-field text-sm mb-4"
            />

            <div className="space-y-4 max-h-[400px] overflow-y-auto">
              {Object.entries(skillTaxonomy).map(([category, skills]) => {
                const filtered = skills.filter(s =>
                  !skillSearch || s.toLowerCase().includes(skillSearch.toLowerCase())
                );
                if (filtered.length === 0) return null;
                return (
                  <div key={category}>
                    <p className="text-xs text-gray-400 uppercase tracking-wider font-medium mb-2">
                      {category.replace(/_/g, ' ')}
                    </p>
                    <div className="flex flex-wrap gap-1.5">
                      {filtered.map(skill => (
                        <button key={skill}
                          onClick={() => toggleSkill(skill)}
                          className={`px-2.5 py-1 rounded-lg text-xs font-medium transition-all ${
                            selectedSkills.includes(skill)
                              ? 'bg-cyan-400/15 text-cyan-400 border border-cyan-400/30'
                              : 'bg-navy-800 text-gray-400 border border-gray-700/30 hover:border-gray-600/50'
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
        </div>
      )}

      {/* Saved Searches Tab */}
      {activeTab === 'searches' && (
        <div className="space-y-4 animate-slide-up">
          {/* Create New */}
          <div className="card p-4">
            <h3 className="text-sm font-semibold text-white mb-3">Create Saved Search</h3>
            <div className="flex gap-2">
              <input
                type="text"
                value={newSearchName}
                onChange={(e) => setNewSearchName(e.target.value)}
                placeholder="Search name (e.g. 'Senior React Remote')"
                className="input-field text-sm flex-1"
                onKeyDown={(e) => e.key === 'Enter' && handleCreateSearch()}
              />
              <button onClick={handleCreateSearch} className="btn-primary text-sm whitespace-nowrap">
                Create
              </button>
            </div>
            <p className="text-xs text-gray-500 mt-2">
              Uses your current role selections ({selectedRoles.length}) and skills ({selectedSkills.length})
            </p>
          </div>

          {/* List */}
          {savedSearches.length === 0 ? (
            <EmptyState icon="🔍" title="No saved searches" description="Create a saved search to get notified about matching jobs." />
          ) : (
            <div className="space-y-2">
              {savedSearches.map(search => (
                <div key={search.id} className="card p-4 flex items-center justify-between">
                  <div className="flex-1">
                    <div className="flex items-center gap-2">
                      <h4 className="text-sm font-medium text-white">{search.name}</h4>
                      {search.is_active && (
                        <span className="px-2 py-0.5 rounded text-[10px] font-medium bg-green-400/10 text-green-400">Active</span>
                      )}
                    </div>
                    <div className="flex items-center gap-3 mt-1">
                      <span className="text-xs text-gray-500">
                        {search.role_categories?.length || 0} roles · {search.skills_filter?.length || 0} skills
                      </span>
                      <span className="text-xs text-gray-500">
                        Score ≥ {search.min_score_threshold}
                      </span>
                      <span className="text-xs text-gray-500">
                        {search.match_count} matches
                      </span>
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    <button onClick={() => handleToggleSearch(search.id)}
                      className={`px-3 py-1 rounded-lg text-xs font-medium transition-all ${
                        search.is_active
                          ? 'bg-yellow-400/10 text-yellow-400 hover:bg-yellow-400/20'
                          : 'bg-green-400/10 text-green-400 hover:bg-green-400/20'
                      }`}>
                      {search.is_active ? 'Pause' : 'Activate'}
                    </button>
                    <button onClick={() => handleDeleteSearch(search.id)}
                      className="px-3 py-1 rounded-lg text-xs font-medium bg-red-400/10 text-red-400 hover:bg-red-400/20 transition-all">
                      Delete
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Preview Tab */}
      {activeTab === 'preview' && (
        <div className="space-y-4 animate-slide-up">
          {preview ? (
            <>
              <div className="card p-5">
                <h3 className="text-sm font-semibold text-cyan-400 mb-3">AI Scoring Profile</h3>
                <p className="text-sm text-gray-300 whitespace-pre-wrap bg-navy-950 p-4 rounded-xl border border-gray-700/30">
                  {preview.profile_text}
                </p>
              </div>

              {preview.search_queries.length > 0 && (
                <div className="card p-5">
                  <h3 className="text-sm font-semibold text-purple-400 mb-3">
                    Generated Search Queries ({preview.search_queries.length})
                  </h3>
                  <div className="space-y-2">
                    {preview.search_queries.map((q, i) => (
                      <div key={i} className="flex items-center gap-2 p-2 rounded-lg bg-navy-950 border border-gray-700/20">
                        <span className="w-6 h-6 rounded-full bg-purple-400/10 text-purple-400 text-xs flex items-center justify-center">
                          {i + 1}
                        </span>
                        <span className="text-sm text-gray-300">{q}</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </>
          ) : (
            <div className="card p-8 text-center">
              <p className="text-gray-400">Save your profile first to see the AI matching preview.</p>
              <button onClick={handleSave} className="btn-primary text-sm mt-4">
                Save & Preview
              </button>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
