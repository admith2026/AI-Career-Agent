'use client';

interface SkillBadgeProps {
  name: string;
  matched?: boolean;
}

export default function SkillBadge({ name, matched = false }: SkillBadgeProps) {
  return (
    <span
      className={`inline-flex items-center px-2.5 py-1 rounded-lg text-xs font-medium transition-colors ${
        matched
          ? 'bg-cyan-400/10 text-cyan-400 border border-cyan-400/20'
          : 'bg-navy-950 text-gray-400 border border-gray-700/50'
      }`}
    >
      {matched && <span className="w-1.5 h-1.5 rounded-full bg-cyan-400 mr-1.5" />}
      {name}
    </span>
  );
}
