'use client';

interface StatCardProps {
  label: string;
  value: number | string;
  icon?: React.ReactNode;
  trend?: { value: number; positive: boolean };
  accent?: 'cyan' | 'gold' | 'green' | 'purple' | 'red';
}

const accentMap = {
  cyan: 'border-cyan-400 shadow-glow',
  gold: 'border-gold-400 shadow-glow-gold',
  green: 'border-green-400',
  purple: 'border-purple-400',
  red: 'border-red-400',
};

const iconBgMap = {
  cyan: 'bg-cyan-400/10 text-cyan-400',
  gold: 'bg-gold-400/10 text-gold-400',
  green: 'bg-green-400/10 text-green-400',
  purple: 'bg-purple-400/10 text-purple-400',
  red: 'bg-red-400/10 text-red-400',
};

export default function StatCard({ label, value, icon, trend, accent = 'cyan' }: StatCardProps) {
  return (
    <div className={`card border-l-4 ${accentMap[accent]} p-5 animate-fade-in`}>
      <div className="flex items-start justify-between">
        <div>
          <p className="stat-value">{value}</p>
          <p className="text-sm text-gray-400 mt-1">{label}</p>
          {trend && (
            <p className={`text-xs mt-2 font-medium ${trend.positive ? 'text-green-400' : 'text-red-400'}`}>
              {trend.positive ? '↑' : '↓'} {Math.abs(trend.value)}% from last week
            </p>
          )}
        </div>
        {icon && (
          <div className={`p-3 rounded-xl ${iconBgMap[accent]}`}>
            {icon}
          </div>
        )}
      </div>
    </div>
  );
}
