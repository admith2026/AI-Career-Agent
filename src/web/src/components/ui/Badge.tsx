'use client';

type Variant = 'cyan' | 'gold' | 'green' | 'red' | 'purple' | 'blue' | 'yellow' | 'orange' | 'gray';

interface BadgeProps {
  children: React.ReactNode;
  variant?: Variant;
  dot?: boolean;
}

const variantMap: Record<Variant, string> = {
  cyan: 'bg-cyan-400/10 text-cyan-400 border-cyan-400/20',
  gold: 'bg-gold-400/10 text-gold-400 border-gold-400/20',
  green: 'bg-green-400/10 text-green-400 border-green-400/20',
  red: 'bg-red-400/10 text-red-400 border-red-400/20',
  purple: 'bg-purple-400/10 text-purple-400 border-purple-400/20',
  blue: 'bg-blue-400/10 text-blue-400 border-blue-400/20',
  yellow: 'bg-yellow-400/10 text-yellow-400 border-yellow-400/20',
  orange: 'bg-orange-400/10 text-orange-400 border-orange-400/20',
  gray: 'bg-gray-400/10 text-gray-400 border-gray-400/20',
};

const dotColorMap: Record<Variant, string> = {
  cyan: 'bg-cyan-400',
  gold: 'bg-gold-400',
  green: 'bg-green-400',
  red: 'bg-red-400',
  purple: 'bg-purple-400',
  blue: 'bg-blue-400',
  yellow: 'bg-yellow-400',
  orange: 'bg-orange-400',
  gray: 'bg-gray-400',
};

export default function Badge({ children, variant = 'cyan', dot = false }: BadgeProps) {
  return (
    <span className={`inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-medium border ${variantMap[variant]}`}>
      {dot && <span className={`w-1.5 h-1.5 rounded-full ${dotColorMap[variant]}`} />}
      {children}
    </span>
  );
}
