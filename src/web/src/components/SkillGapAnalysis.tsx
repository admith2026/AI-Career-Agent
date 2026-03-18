'use client';

import { useState } from 'react';
import { Badge, ProgressBar, SkillBadge } from '@/components/ui';

interface Skill {
  name: string;
  level: 'strong' | 'moderate' | 'gap';
  score: number;
  demand: number;
  recommendation?: string;
}

const MOCK_SKILLS: Skill[] = [
  { name: 'Python', level: 'strong', score: 92, demand: 95, recommendation: 'Keep current with Python 3.12 features' },
  { name: 'React', level: 'strong', score: 88, demand: 90 },
  { name: 'TypeScript', level: 'strong', score: 85, demand: 88 },
  { name: 'PostgreSQL', level: 'strong', score: 82, demand: 75 },
  { name: 'Docker', level: 'strong', score: 80, demand: 85 },
  { name: 'Kubernetes', level: 'moderate', score: 55, demand: 78, recommendation: 'Focus on K8s deployments and Helm charts to unlock senior DevOps roles' },
  { name: 'GraphQL', level: 'moderate', score: 50, demand: 65, recommendation: 'Learn Apollo Server/Client — common in modern API architectures' },
  { name: 'Redis', level: 'moderate', score: 60, demand: 70 },
  { name: 'AWS', level: 'moderate', score: 58, demand: 82, recommendation: 'AWS certifications can boost match scores by 10-15%' },
  { name: 'Rust', level: 'gap', score: 15, demand: 45, recommendation: 'Emerging for systems programming — learning Rust opens high-comp roles' },
  { name: 'Go', level: 'gap', score: 20, demand: 60, recommendation: 'High demand in infrastructure/cloud. Start with microservices in Go' },
  { name: 'Terraform', level: 'gap', score: 10, demand: 72, recommendation: 'Critical for IaC roles. Pair with AWS knowledge for maximum impact' },
];

const levelConfig = {
  strong: { label: 'Strong', color: 'green' as const, icon: '✅', bg: 'bg-green-500/10 border-green-500/20' },
  moderate: { label: 'Moderate', color: 'gold' as const, icon: '⚠️', bg: 'bg-gold-400/10 border-gold-400/20' },
  gap: { label: 'Gap', color: 'red' as const, icon: '❌', bg: 'bg-red-500/10 border-red-500/20' },
};

export default function SkillGapAnalysis() {
  const [skills] = useState(MOCK_SKILLS);
  const [selectedLevel, setSelectedLevel] = useState<string | null>(null);
  const [expandedSkill, setExpandedSkill] = useState<string | null>(null);

  const filtered = selectedLevel ? skills.filter((s) => s.level === selectedLevel) : skills;
  const strongCount = skills.filter((s) => s.level === 'strong').length;
  const moderateCount = skills.filter((s) => s.level === 'moderate').length;
  const gapCount = skills.filter((s) => s.level === 'gap').length;
  const avgScore = Math.round(skills.reduce((sum, s) => sum + s.score, 0) / skills.length);

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="page-title">Skill Gap Analysis</h1>
          <p className="text-gray-400 text-sm mt-1">AI-powered skill assessment &amp; recommendations</p>
        </div>
        <Badge variant="purple" dot>AI Analyzed</Badge>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="card p-4 text-center">
          <p className="text-3xl font-bold gradient-text">{avgScore}</p>
          <p className="text-xs text-gray-500 mt-1 uppercase tracking-wider">Overall Score</p>
        </div>
        <div className="card p-4 text-center cursor-pointer hover:border-green-500/30 transition-colors" onClick={() => setSelectedLevel(selectedLevel === 'strong' ? null : 'strong')}>
          <p className="text-3xl font-bold text-green-400">{strongCount}</p>
          <p className="text-xs text-gray-500 mt-1 uppercase tracking-wider">Strong Skills</p>
        </div>
        <div className="card p-4 text-center cursor-pointer hover:border-gold-400/30 transition-colors" onClick={() => setSelectedLevel(selectedLevel === 'moderate' ? null : 'moderate')}>
          <p className="text-3xl font-bold text-gold-400">{moderateCount}</p>
          <p className="text-xs text-gray-500 mt-1 uppercase tracking-wider">Moderate</p>
        </div>
        <div className="card p-4 text-center cursor-pointer hover:border-red-500/30 transition-colors" onClick={() => setSelectedLevel(selectedLevel === 'gap' ? null : 'gap')}>
          <p className="text-3xl font-bold text-red-400">{gapCount}</p>
          <p className="text-xs text-gray-500 mt-1 uppercase tracking-wider">Gaps</p>
        </div>
      </div>

      {/* Skill vs Demand Visualization */}
      <div className="card p-6">
        <h2 className="section-title mb-1">Skill Level vs. Market Demand</h2>
        <p className="text-xs text-gray-500 mb-4">Green bars = your skill level · Gray bars = market demand</p>
        <div className="space-y-4">
          {filtered.map((skill) => {
            const cfg = levelConfig[skill.level];
            const expanded = expandedSkill === skill.name;
            return (
              <div key={skill.name}>
                <div
                  className="flex items-center gap-3 cursor-pointer group"
                  onClick={() => setExpandedSkill(expanded ? null : skill.name)}
                >
                  <span className="text-sm text-gray-300 w-24 truncate font-medium">{skill.name}</span>
                  <div className="flex-1 space-y-1">
                    {/* Skill */}
                    <div className="flex items-center gap-2">
                      <div className="flex-1 h-2 bg-navy-950 rounded-full overflow-hidden">
                        <div
                          className={`h-full rounded-full transition-all duration-700 ${
                            skill.level === 'strong' ? 'bg-gradient-to-r from-green-500 to-emerald-400' :
                            skill.level === 'moderate' ? 'bg-gradient-to-r from-gold-400 to-yellow-400' :
                            'bg-gradient-to-r from-red-500 to-red-400'
                          }`}
                          style={{ width: `${skill.score}%` }}
                        />
                      </div>
                      <span className="text-xs text-white font-medium w-8 text-right">{skill.score}</span>
                    </div>
                    {/* Demand */}
                    <div className="flex items-center gap-2">
                      <div className="flex-1 h-1.5 bg-navy-950 rounded-full overflow-hidden">
                        <div
                          className="h-full rounded-full bg-gray-600/50"
                          style={{ width: `${skill.demand}%` }}
                        />
                      </div>
                      <span className="text-[10px] text-gray-500 w-8 text-right">{skill.demand}</span>
                    </div>
                  </div>
                  <Badge variant={cfg.color === 'gold' ? 'gold' : cfg.color === 'green' ? 'green' : 'red'}>
                    {cfg.icon} {cfg.label}
                  </Badge>
                  <svg className={`w-4 h-4 text-gray-500 transition-transform ${expanded ? 'rotate-180' : ''}`} fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                  </svg>
                </div>
                {/* Expanded recommendation */}
                {expanded && skill.recommendation && (
                  <div className={`mt-2 ml-[108px] p-3 rounded-xl border ${cfg.bg} animate-slide-up`}>
                    <p className="text-xs text-gray-400 uppercase tracking-wider mb-1">AI Recommendation</p>
                    <p className="text-sm text-gray-300">{skill.recommendation}</p>
                    {skill.level !== 'strong' && (
                      <p className="text-xs text-cyan-400 mt-2">
                        Improving this skill could increase match scores by ~{skill.level === 'gap' ? '10-15' : '5-8'}%
                      </p>
                    )}
                  </div>
                )}
              </div>
            );
          })}
        </div>
      </div>

      {/* Quick skill badge overview */}
      <div className="card p-6">
        <h2 className="section-title mb-3">Your Skills at a Glance</h2>
        <div className="flex flex-wrap gap-2">
          {skills.map((s) => (
            <SkillBadge key={s.name} name={s.name} matched={s.level !== 'gap'} />
          ))}
        </div>
      </div>
    </div>
  );
}
