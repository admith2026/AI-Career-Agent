'use client';

interface MatchScoreProps {
  score: number;
  size?: 'sm' | 'md' | 'lg';
  showLabel?: boolean;
}

export default function MatchScore({ score, size = 'md', showLabel = true }: MatchScoreProps) {
  const sizeMap = {
    sm: { ring: 40, stroke: 3, text: 'text-xs', label: 'text-[10px]' },
    md: { ring: 56, stroke: 4, text: 'text-sm', label: 'text-xs' },
    lg: { ring: 80, stroke: 5, text: 'text-xl', label: 'text-sm' },
  };
  const s = sizeMap[size];
  const radius = (s.ring - s.stroke * 2) / 2;
  const circumference = 2 * Math.PI * radius;
  const offset = circumference - (score / 100) * circumference;

  const color =
    score >= 80 ? '#22D3EE' :
    score >= 60 ? '#22D3EE' :
    score >= 40 ? '#FACC15' :
    '#EF4444';

  const bgColor =
    score >= 80 ? 'rgba(34,211,238,0.1)' :
    score >= 60 ? 'rgba(34,211,238,0.08)' :
    score >= 40 ? 'rgba(250,204,21,0.1)' :
    'rgba(239,68,68,0.1)';

  return (
    <div className="flex flex-col items-center gap-1">
      <div className="relative" style={{ width: s.ring, height: s.ring }}>
        <svg width={s.ring} height={s.ring} className="-rotate-90">
          <circle
            cx={s.ring / 2}
            cy={s.ring / 2}
            r={radius}
            fill={bgColor}
            stroke="rgba(255,255,255,0.05)"
            strokeWidth={s.stroke}
          />
          <circle
            cx={s.ring / 2}
            cy={s.ring / 2}
            r={radius}
            fill="none"
            stroke={color}
            strokeWidth={s.stroke}
            strokeLinecap="round"
            strokeDasharray={circumference}
            strokeDashoffset={offset}
            className="transition-all duration-700 ease-out"
          />
        </svg>
        <span className={`absolute inset-0 flex items-center justify-center font-bold ${s.text}`} style={{ color }}>
          {score}
        </span>
      </div>
      {showLabel && <span className={`${s.label} text-gray-500`}>Match</span>}
    </div>
  );
}
