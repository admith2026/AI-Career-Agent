'use client';

import { useEffect, useState } from 'react';
import { billingApi } from '@/lib/api';
import { Badge, LoadingSpinner, StatCard, EmptyState } from '@/components/ui';

interface Plan { id: string; name: string; price: number; monthly_applications: number; features: Record<string, boolean>; }
interface Sub { id: string; plan: string; plan_details: Plan; status: string; monthly_applications_limit: number; monthly_applications_used: number; features: Record<string, boolean>; current_period_end: string | null; cancel_at_period_end: boolean; }
interface Usage { records_count: number; total_credits: number; by_type: Record<string, number>; }

export default function SubscriptionView() {
  const [plans, setPlans] = useState<Plan[]>([]);
  const [sub, setSub] = useState<Sub | null>(null);
  const [usage, setUsage] = useState<Usage | null>(null);
  const [loading, setLoading] = useState(true);
  const [tab, setTab] = useState<'plans' | 'usage'>('plans');

  const load = () => {
    setLoading(true);
    Promise.all([
      billingApi.getPlans().then(r => { const d = r.data?.plans ?? r.data; setPlans(Array.isArray(d) ? d : []); }).catch(() => {}),
      billingApi.getSubscription().then(r => setSub(r.data)).catch(() => {}),
      billingApi.getUsage().then(r => setUsage(r.data)).catch(() => {}),
    ]).finally(() => setLoading(false));
  };

  useEffect(() => { load(); }, []);

  const handleSubscribe = (plan: string) => {
    billingApi.subscribe(plan).then(() => load());
  };

  const handleCancel = () => {
    billingApi.cancel().then(() => load());
  };

  if (loading) return <LoadingSpinner text="Loading subscription..." />;

  const PLAN_ICONS: Record<string, string> = { free: '🆓', starter: '🚀', pro: '⚡', enterprise: '🏢' };
  const PLAN_COLORS: Record<string, string> = { free: 'border-gray-600', starter: 'border-blue-500', pro: 'border-purple-500', enterprise: 'border-yellow-500' };

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="page-title">Subscription & Billing</h1>
          <p className="text-gray-400 text-sm mt-1">Manage your plan, usage & billing</p>
        </div>
        {sub && <Badge variant={sub.plan === 'pro' ? 'purple' : sub.plan === 'enterprise' ? 'yellow' : 'blue'}>{sub.plan.toUpperCase()}</Badge>}
      </div>

      {sub && (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <StatCard label="Current Plan" value={sub.plan.charAt(0).toUpperCase() + sub.plan.slice(1)} icon={PLAN_ICONS[sub.plan] ?? '📦'} />
          <StatCard label="Applications Used" value={`${sub.monthly_applications_used}/${sub.monthly_applications_limit === -1 ? '∞' : sub.monthly_applications_limit}`} icon="📝" />
          <StatCard label="Credits Used" value={usage?.total_credits ?? 0} icon="🪙" />
          <StatCard label="Period Ends" value={sub.current_period_end ? new Date(sub.current_period_end).toLocaleDateString() : '-'} icon="📅" />
        </div>
      )}

      <div className="flex gap-2 border-b border-gray-700/30 pb-2">
        {(['plans', 'usage'] as const).map(t => (
          <button key={t} onClick={() => setTab(t)}
            className={`px-4 py-2 rounded-t-lg text-sm font-medium transition-all capitalize ${tab === t ? 'bg-purple-500/20 text-purple-400 border-b-2 border-purple-400' : 'text-gray-400 hover:text-white'}`}>
            {t}
          </button>
        ))}
      </div>

      {tab === 'plans' && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {plans.map(p => (
            <div key={p.id} className={`glass-card p-6 rounded-xl border-2 ${sub?.plan === p.id ? 'border-purple-500 ring-2 ring-purple-500/30' : PLAN_COLORS[p.id] ?? 'border-gray-700'}`}>
              <div className="text-3xl mb-2">{PLAN_ICONS[p.id] ?? '📦'}</div>
              <h3 className="text-white text-lg font-bold">{p.name}</h3>
              <div className="text-3xl font-bold text-white mt-2">
                ${p.price}<span className="text-sm text-gray-400 font-normal">/mo</span>
              </div>
              <div className="text-sm text-gray-400 mt-1">
                {p.monthly_applications === -1 ? 'Unlimited' : p.monthly_applications} applications/mo
              </div>
              <ul className="mt-4 space-y-2">
                {Object.entries(p.features ?? {}).map(([k, v]) => (
                  <li key={k} className={`text-sm flex items-center gap-2 ${v ? 'text-green-400' : 'text-gray-600'}`}>
                    {v ? '✓' : '✗'} {k.replace(/_/g, ' ')}
                  </li>
                ))}
              </ul>
              <button
                onClick={() => handleSubscribe(p.id)}
                disabled={sub?.plan === p.id}
                className={`mt-4 w-full py-2 rounded-lg text-sm font-semibold transition-all ${sub?.plan === p.id ? 'bg-gray-700 text-gray-400 cursor-default' : 'bg-purple-600 text-white hover:bg-purple-500'}`}
              >
                {sub?.plan === p.id ? 'Current Plan' : 'Select Plan'}
              </button>
            </div>
          ))}
        </div>
      )}

      {tab === 'usage' && (
        <div className="space-y-4">
          {usage && Object.keys(usage.by_type).length > 0 ? (
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              {Object.entries(usage.by_type).map(([type, credits]) => (
                <div key={type} className="glass-card p-4 rounded-xl">
                  <h4 className="text-white font-medium capitalize">{type.replace(/_/g, ' ')}</h4>
                  <p className="text-2xl font-bold text-purple-400 mt-1">{credits}</p>
                  <p className="text-xs text-gray-400">credits used</p>
                </div>
              ))}
            </div>
          ) : (
            <EmptyState icon="🪙" title="No usage recorded" description="Start using AI features to see usage stats" />
          )}
          {sub && !sub.cancel_at_period_end && sub.plan !== 'free' && (
            <button onClick={handleCancel} className="text-sm text-red-400 hover:text-red-300 border border-red-500/30 px-4 py-2 rounded-lg">
              Cancel Subscription
            </button>
          )}
          {sub?.cancel_at_period_end && (
            <p className="text-sm text-yellow-400">⚠️ Subscription will be canceled at the end of the current period.</p>
          )}
        </div>
      )}
    </div>
  );
}
