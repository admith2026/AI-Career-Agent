'use client';

interface ProgressBarProps {
  value: number;
  max?: number;
  color?: 'cyan' | 'gold' | 'green' | 'purple' | 'red';
  height?: 'sm' | 'md';
  showLabel?: boolean;
}

const colorMap = {
  cyan: 'bg-gradient-to-r from-cyan-500 to-cyan-400',
  gold: 'bg-gradient-to-r from-gold-500 to-gold-400',
  green: 'bg-gradient-to-r from-green-500 to-green-400',
  purple: 'bg-gradient-to-r from-purple-500 to-purple-400',
  red: 'bg-gradient-to-r from-red-500 to-red-400',
};

export default function ProgressBar({ value, max = 100, color = 'cyan', height = 'sm', showLabel = false }: ProgressBarProps) {
  const pct = Math.min(100, Math.max(0, (value / max) * 100));
  return (
    <div className="flex items-center gap-2">
      <div className={`flex-1 bg-navy-950 rounded-full overflow-hidden ${height === 'sm' ? 'h-1.5' : 'h-2.5'}`}>
        <div
          className={`${colorMap[color]} rounded-full transition-all duration-700 ease-out ${height === 'sm' ? 'h-1.5' : 'h-2.5'}`}
          style={{ width: `${pct}%` }}
        />
      </div>
      {showLabel && <span className="text-xs text-gray-400 w-10 text-right">{Math.round(pct)}%</span>}
    </div>
  );
}
