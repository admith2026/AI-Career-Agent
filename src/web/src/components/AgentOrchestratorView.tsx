'use client';

import { useEffect, useState } from 'react';
import { agentsApi } from '@/lib/api';
import { Badge, LoadingSpinner, StatCard, EmptyState } from '@/components/ui';

interface AgentStatus { status: string; service_url: string; }
interface Task { id: string; agent_type: string; task_type: string; status: string; priority: number; created_at: string | null; }
interface Workflow { id: string; name: string; description: string; trigger: string; steps_count: number; is_active: boolean; run_count: number; last_run_at: string | null; }
interface Stats { total_tasks: number; running: number; completed: number; failed: number; workflows: number; agents_available: number; }
interface McpTool { name: string; description: string; category: string; parameters: { name: string; type: string; required: boolean; description: string; }[]; }

const STATUS_COLORS: Record<string, string> = { online: 'bg-green-500', offline: 'bg-red-500', queued: 'bg-yellow-500', running: 'bg-blue-500', completed: 'bg-green-500', failed: 'bg-red-500', canceled: 'bg-gray-500' };

export default function AgentOrchestratorView() {
  const [agents, setAgents] = useState<Record<string, AgentStatus>>({});
  const [tasks, setTasks] = useState<Task[]>([]);
  const [workflows, setWorkflows] = useState<Workflow[]>([]);
  const [stats, setStats] = useState<Stats | null>(null);
  const [mcpTools, setMcpTools] = useState<McpTool[]>([]);
  const [mcpResult, setMcpResult] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [tab, setTab] = useState<'agents' | 'tasks' | 'workflows' | 'pipeline' | 'planner' | 'activity' | 'mcp'>('agents');
  const [pipelineResult, setPipelineResult] = useState<any>(null);
  const [planGoal, setPlanGoal] = useState('');
  const [planResult, setPlanResult] = useState<any>(null);
  const [planLoading, setPlanLoading] = useState(false);
  const [activity, setActivity] = useState<any[]>([]);
  const [activityLoading, setActivityLoading] = useState(false);

  const load = () => {
    setLoading(true);
    Promise.all([
      agentsApi.getStatus().then(r => { const d = r.data?.agents; setAgents(typeof d === 'object' && d !== null && !Array.isArray(d) ? d : {}); }).catch(() => {}),
      agentsApi.getTasks().then(r => { const d = r.data?.tasks ?? r.data; setTasks(Array.isArray(d) ? d : []); }).catch(() => {}),
      agentsApi.getWorkflows().then(r => { const d = r.data?.workflows ?? r.data; setWorkflows(Array.isArray(d) ? d : []); }).catch(() => {}),
      agentsApi.getStats().then(r => setStats(r.data)).catch(() => {}),
      agentsApi.getMcpTools?.().then(r => { const d = r.data?.tools ?? r.data; setMcpTools(Array.isArray(d) ? d : []); }).catch(() => {}),
    ]).finally(() => setLoading(false));
  };

  useEffect(() => { load(); }, []);

  const invokeTool = async (toolName: string) => {
    setMcpResult(null);
    try {
      const res = await agentsApi.invokeMcpTool(toolName, {});
      setMcpResult(res.data);
    } catch {
      setMcpResult({ error: 'Tool invocation failed' });
    }
  };

  const runPipeline = () => {
    agentsApi.runPipeline().then(r => { setPipelineResult(r.data); load(); }).catch(() => setPipelineResult({ error: 'Failed' }));
  };

  const createPlan = async () => {
    if (!planGoal.trim()) return;
    setPlanLoading(true);
    setPlanResult(null);
    try {
      const res = await agentsApi.createPlan(planGoal);
      setPlanResult(res.data);
      load();
    } catch {
      setPlanResult({ error: 'Planning failed. Check agent orchestrator service.' });
    } finally {
      setPlanLoading(false);
    }
  };

  const loadActivity = async () => {
    setActivityLoading(true);
    try {
      const res = await agentsApi.getActivity(30);
      const d = res.data?.activity ?? res.data;
      setActivity(Array.isArray(d) ? d : []);
    } catch {
      setActivity([]);
    } finally {
      setActivityLoading(false);
    }
  };

  const executeTask = async (taskId: string) => {
    try {
      await agentsApi.executeTask(taskId);
      load();
    } catch { /* ignore */ }
  };

  const toggleWorkflow = (id: string, active: boolean) => {
    agentsApi.toggleWorkflow(id, !active).then(() => load());
  };

  const runWorkflow = (id: string) => {
    agentsApi.runWorkflow(id).then(() => load());
  };

  if (loading) return <LoadingSpinner text="Initializing agent network..." />;

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="page-title">Agent Orchestrator</h1>
          <p className="text-gray-400 text-sm mt-1">Multi-agent coordination, workflows & automation pipeline</p>
        </div>
        <Badge variant="purple" dot>AI Agents</Badge>
      </div>

      {stats && (
        <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-4">
          <StatCard label="Total Tasks" value={stats.total_tasks} icon="📋" />
          <StatCard label="Running" value={stats.running} icon="⚡" />
          <StatCard label="Completed" value={stats.completed} icon="✅" />
          <StatCard label="Failed" value={stats.failed} icon="❌" />
          <StatCard label="Workflows" value={stats.workflows} icon="🔄" />
          <StatCard label="Agents" value={stats.agents_available} icon="🤖" />
        </div>
      )}

      <div className="flex gap-2 border-b border-gray-700/30 pb-2">
        {(['agents', 'tasks', 'workflows', 'pipeline', 'planner', 'activity', 'mcp'] as const).map(t => (
          <button key={t} onClick={() => { setTab(t); if (t === 'activity') loadActivity(); }}
            className={`px-4 py-2 rounded-t-lg text-sm font-medium transition-all capitalize ${tab === t ? 'bg-purple-500/20 text-purple-400 border-b-2 border-purple-400' : 'text-gray-400 hover:text-white'}`}>
            {t === 'mcp' ? '🔧 MCP Tools' : t === 'planner' ? '🧠 AI Planner' : t === 'activity' ? '📡 Activity' : t}
          </button>
        ))}
      </div>

      {tab === 'agents' && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {Object.entries(agents).map(([name, info]) => (
            <div key={name} className="glass-card p-4 rounded-xl">
              <div className="flex items-center justify-between mb-2">
                <h3 className="text-white font-semibold capitalize">{name.replace('_', ' ')}</h3>
                <span className={`w-3 h-3 rounded-full ${STATUS_COLORS[info.status] ?? 'bg-gray-500'}`} />
              </div>
              <p className="text-sm text-gray-400">Status: <span className={info.status === 'online' ? 'text-green-400' : 'text-red-400'}>{info.status}</span></p>
            </div>
          ))}
          {Object.keys(agents).length === 0 && <EmptyState icon="🤖" title="No agents detected" description="Agent services may be offline" />}
        </div>
      )}

      {tab === 'tasks' && (
        <div className="space-y-3">
          {tasks.map(t => (
            <div key={t.id} className="glass-card p-4 rounded-xl flex items-center justify-between">
              <div>
                <span className="text-white font-medium capitalize">{t.agent_type}</span>
                <span className="text-gray-400 ml-2">→ {t.task_type}</span>
                {t.created_at && <span className="text-gray-500 text-xs ml-3">{new Date(t.created_at).toLocaleString()}</span>}
              </div>
              <div className="flex items-center gap-2">
                <span className="text-xs text-gray-400">P{t.priority}</span>
                <Badge variant={t.status === 'completed' ? 'green' : t.status === 'running' ? 'blue' : t.status === 'failed' ? 'red' : 'gray'}>{t.status}</Badge>
                {(t.status === 'queued' || t.status === 'failed') && (
                  <button onClick={() => executeTask(t.id)} className="text-xs px-2 py-1 bg-purple-600 rounded hover:bg-purple-500 text-white">▶ Run</button>
                )}
              </div>
            </div>
          ))}
          {tasks.length === 0 && <EmptyState icon="📋" title="No tasks yet" description="Create a task or run the pipeline" />}
        </div>
      )}

      {tab === 'workflows' && (
        <div className="space-y-3">
          {workflows.map(w => (
            <div key={w.id} className="glass-card p-4 rounded-xl">
              <div className="flex items-center justify-between mb-2">
                <h3 className="text-white font-semibold">{w.name}</h3>
                <div className="flex items-center gap-2">
                  <Badge variant={w.is_active ? 'green' : 'gray'}>{w.is_active ? 'Active' : 'Inactive'}</Badge>
                  <button onClick={() => toggleWorkflow(w.id, w.is_active)} className="text-xs px-2 py-1 bg-gray-700 rounded hover:bg-gray-600 text-gray-300">{w.is_active ? 'Disable' : 'Enable'}</button>
                  <button onClick={() => runWorkflow(w.id)} className="text-xs px-2 py-1 bg-purple-600 rounded hover:bg-purple-500 text-white">Run</button>
                </div>
              </div>
              <p className="text-sm text-gray-400">{w.description || 'No description'}</p>
              <div className="flex gap-4 mt-2 text-xs text-gray-500">
                <span>{w.steps_count} steps</span>
                <span>Trigger: {w.trigger}</span>
                <span>Runs: {w.run_count}</span>
                {w.last_run_at && <span>Last: {new Date(w.last_run_at).toLocaleString()}</span>}
              </div>
            </div>
          ))}
          {workflows.length === 0 && <EmptyState icon="🔄" title="No workflows" description="Create an agent workflow to automate tasks" />}
        </div>
      )}

      {tab === 'pipeline' && (
        <div className="space-y-4">
          <div className="glass-card p-6 rounded-xl text-center">
            <h3 className="text-xl text-white font-bold mb-2">Full Automation Pipeline</h3>
            <p className="text-gray-400 mb-4">Discover → Score → Apply → Outreach → Follow-up</p>
            <button onClick={runPipeline} className="bg-gradient-to-r from-purple-600 to-pink-600 text-white px-8 py-3 rounded-xl font-semibold hover:opacity-90 transition-all">
              🚀 Launch Pipeline
            </button>
            {pipelineResult && (
              <div className="mt-4 p-4 bg-gray-800/50 rounded-lg text-left">
                <p className="text-green-400 font-medium">Pipeline launched!</p>
                <p className="text-gray-400 text-sm">Tasks created: {pipelineResult.tasks_created ?? pipelineResult.error}</p>
              </div>
            )}
          </div>
          <div className="grid grid-cols-5 gap-2">
            {['🔍 Discovery', '🎯 Matching', '📝 Application', '📤 Outreach', '📞 Follow-up'].map((step, i) => (
              <div key={i} className="glass-card p-3 rounded-xl text-center">
                <div className="text-2xl mb-1">{step.split(' ')[0]}</div>
                <div className="text-xs text-gray-400">{step.split(' ').slice(1).join(' ')}</div>
              </div>
            ))}
          </div>
        </div>
      )}

      {tab === 'planner' && (
        <div className="space-y-4">
          <div className="glass-card p-6 rounded-xl">
            <h3 className="text-lg text-white font-bold mb-1">🧠 AI Career Planner</h3>
            <p className="text-gray-400 text-sm mb-4">Describe your career goal and the AI will create an execution plan</p>
            <div className="flex gap-3">
              <input
                type="text"
                value={planGoal}
                onChange={e => setPlanGoal(e.target.value)}
                onKeyDown={e => e.key === 'Enter' && createPlan()}
                placeholder="e.g. Find remote senior React jobs and apply to top matches..."
                className="input-field flex-1"
              />
              <button onClick={createPlan} disabled={planLoading}
                className="bg-gradient-to-r from-purple-600 to-cyan-600 text-white px-6 py-2 rounded-xl font-semibold hover:opacity-90 transition-all disabled:opacity-50">
                {planLoading ? '⏳ Planning...' : '🚀 Plan & Execute'}
              </button>
            </div>
          </div>
          {planResult && !planResult.error && (
            <div className="glass-card p-6 rounded-xl space-y-4">
              <div className="flex items-center justify-between">
                <h4 className="text-white font-bold">{planResult.plan_name || 'Career Plan'}</h4>
                <Badge variant="green">Created</Badge>
              </div>
              {planResult.reasoning && <p className="text-gray-400 text-sm">{planResult.reasoning}</p>}
              <div className="space-y-2">
                {(Array.isArray(planResult.steps) ? planResult.steps : Array.isArray(planResult.tasks_created_ids) ? planResult.tasks_created_ids : []).map((step: any, i: number) => (
                  <div key={i} className="flex items-center gap-3 p-3 bg-navy-950/50 rounded-lg">
                    <span className="text-xs font-bold text-purple-400 w-6 h-6 flex items-center justify-center rounded-full bg-purple-400/10">{i + 1}</span>
                    <div className="flex-1">
                      <span className="text-white text-sm capitalize">{step.agent_type || 'task'}</span>
                      <span className="text-gray-400 text-sm ml-2">→ {step.task_type || step}</span>
                    </div>
                    {step.priority && <span className="text-xs text-gray-500">P{step.priority}</span>}
                  </div>
                ))}
              </div>
              {Array.isArray(planResult.tasks_created_ids) && (
                <p className="text-cyan-400 text-sm">✅ {planResult.tasks_created_ids.length} tasks created and queued for execution</p>
              )}
            </div>
          )}
          {planResult?.error && (
            <div className="glass-card p-4 rounded-xl text-red-400 text-sm">{planResult.error}</div>
          )}
        </div>
      )}

      {tab === 'activity' && (
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="text-lg text-white font-bold">📡 Real-Time Activity Feed</h3>
            <button onClick={loadActivity} className="text-xs px-3 py-1.5 bg-gray-700 rounded hover:bg-gray-600 text-gray-300">↻ Refresh</button>
          </div>
          {activityLoading ? (
            <LoadingSpinner text="Loading activity..." />
          ) : activity.length === 0 ? (
            <EmptyState icon="📡" title="No recent activity" description="Activity will appear as agents process tasks" />
          ) : (
            <div className="space-y-2">
              {activity.map((item: any, i: number) => (
                <div key={i} className="glass-card p-3 rounded-xl flex items-center gap-3">
                  <span className="text-lg">
                    {item.type === 'task' ? '⚙️' : item.type === 'application' ? '📝' : '🤖'}
                  </span>
                  <div className="flex-1 min-w-0">
                    <p className="text-sm text-white truncate">{item.description || item.title || `${item.type} event`}</p>
                    <p className="text-xs text-gray-500">{item.timestamp ? new Date(item.timestamp).toLocaleString() : ''}</p>
                  </div>
                  {item.status && (
                    <Badge variant={item.status === 'completed' ? 'green' : item.status === 'failed' ? 'red' : 'gray'}>{item.status}</Badge>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {tab === 'mcp' && (
        <div className="space-y-4">
          <div className="glass-card p-6 rounded-xl">
            <h3 className="text-lg text-white font-bold mb-1">MCP Tool Registry</h3>
            <p className="text-gray-400 text-sm mb-4">Model Context Protocol tools available for AI agent invocation</p>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              {mcpTools.map(tool => (
                <div key={tool.name} className="glass-card p-4 rounded-xl border border-gray-700/30 hover:border-purple-400/30 transition-all">
                  <div className="flex items-center justify-between mb-2">
                    <h4 className="text-sm font-semibold text-white">{tool.name.replace(/_/g, ' ')}</h4>
                    <Badge variant="purple">{tool.category}</Badge>
                  </div>
                  <p className="text-xs text-gray-400 mb-3">{tool.description}</p>
                  {tool.parameters?.length > 0 && (
                    <div className="flex flex-wrap gap-1 mb-3">
                      {tool.parameters.map(p => (
                        <span key={p.name} className={`text-[10px] px-1.5 py-0.5 rounded ${p.required ? 'bg-cyan-400/10 text-cyan-400' : 'bg-gray-700 text-gray-500'}`}>
                          {p.name}{p.required ? '*' : ''}
                        </span>
                      ))}
                    </div>
                  )}
                  <button onClick={() => invokeTool(tool.name)}
                    className="text-xs px-3 py-1.5 bg-purple-600/20 text-purple-400 rounded-lg hover:bg-purple-600/30 transition-all">
                    ▶ Invoke
                  </button>
                </div>
              ))}
            </div>
            {mcpTools.length === 0 && <EmptyState icon="🔧" title="No MCP tools loaded" description="MCP tools will be available when the agent orchestrator service is running" />}
          </div>
          {mcpResult && (
            <div className="glass-card p-4 rounded-xl">
              <h4 className="text-sm font-semibold text-white mb-2">Tool Result</h4>
              <pre className="text-xs text-gray-300 bg-navy-950 p-3 rounded-lg overflow-auto max-h-64">
                {JSON.stringify(mcpResult, null, 2)}
              </pre>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
