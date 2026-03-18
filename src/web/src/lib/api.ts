import axios from 'axios';

const api = axios.create({
  baseURL: '/api',
  headers: { 'Content-Type': 'application/json' },
});

api.interceptors.request.use((config) => {
  if (typeof window !== 'undefined') {
    const token = localStorage.getItem('token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
  }
  return config;
});

// Auth
export const authApi = {
  login: (email: string, password: string) =>
    api.post('/auth/login', { email, password }),
  register: (email: string, fullName: string, password: string) =>
    api.post('/auth/register', { email, full_name: fullName, password }),
};

// Jobs
export const jobsApi = {
  getJobs: (params?: {
    page?: number; pageSize?: number; source?: string; sources?: string[];
    remote_only?: boolean; min_score?: number; max_score?: number;
    search?: string; technologies?: string[]; contract_types?: string[];
    locations?: string[]; companies?: string[]; has_recruiter?: boolean;
    seniority?: string[]; date_from?: string; sort_by?: string; sort_order?: string;
    role_categories?: string[]; skills?: string[];
    visa_sponsorship?: boolean; experience_min?: number; experience_max?: number;
  }) => api.get('/jobs', { params }),
  getJob: (id: string) => api.get(`/jobs/${id}`),
  getStats: () => api.get('/jobs/stats'),
  getCrawlLogs: () => api.get('/crawl/stats'),
  getFilterOptions: () => api.get('/jobs/filter-options'),
  semanticSearch: (query: string, skills?: string[], limit?: number) =>
    api.post('/semantic-search', { query, skills, limit }),
  getVectorStats: () => api.get('/vector-stats'),
};

// Applications
export const applicationsApi = {
  apply: (jobId: string) =>
    api.post('/applications', { job_id: jobId }),
  getUserApplications: (page = 1, status?: string) =>
    api.get('/applications', { params: { page, status } }),
  getApplication: (id: string) => api.get(`/applications/${id}`),
  updateStatus: (id: string, status: string, notes?: string) =>
    api.patch(`/applications/${id}`, { status, notes }),
  getStats: () => api.get('/applications/stats/summary'),
  // Auto-apply
  getAutoApplySettings: () => api.get('/auto-apply/settings'),
  updateAutoApplySettings: (data: any) => api.post('/auto-apply/settings', data),
  triggerAutoApply: (params?: { min_score?: number; max_count?: number }) =>
    api.post('/auto-apply/trigger', null, { params }),
  getFollowUps: (days?: number) => api.get('/follow-ups', { params: { days_threshold: days } }),
};

// Profile
export const profileApi = {
  getProfile: () => api.get('/profile'),
  updateProfile: (data: any) => api.put('/profile', data),
  updateNotifications: (prefs: any) => api.put('/profile/notifications', prefs),
};

// Resume
export const resumeApi = {
  generate: (data: any) => api.post('/generate-resume', data),
};

// Crawl Engine
export const crawlApi = {
  getSources: () => api.get('/crawl/sources'),
  triggerCrawl: (sourceName: string) => api.post(`/crawl/trigger/${sourceName}`),
  getStats: () => api.get('/crawl/stats'),
  getQueue: () => api.get('/crawl/queue'),
};

// Data Pipeline
export const pipelineApi = {
  getStats: () => api.get('/pipeline/stats'),
  getEvents: (limit = 50) => api.get('/pipeline/events', { params: { limit } }),
  getSignals: (limit = 50) => api.get('/pipeline/signals', { params: { limit } }),
};

// Knowledge Graph
export const graphApi = {
  getCompany: (name: string) => api.get(`/graph/company/${encodeURIComponent(name)}`),
  getHotspots: (limit = 20) => api.get('/graph/hotspots', { params: { limit } }),
  getTechDemand: (limit = 20) => api.get('/graph/technology-demand', { params: { limit } }),
  getStats: () => api.get('/graph/stats'),
  // Recruiter Intelligence
  trackRecruiterInteraction: (email: string, data: { interaction_type: string; sentiment?: string; notes?: string }) =>
    api.post(`/graph/recruiter/${encodeURIComponent(email)}/interaction`, data),
  getRecruiterRankings: (limit = 20) => api.get('/graph/recruiter-rankings', { params: { limit } }),
  getCompanyRecruiters: (company: string) => api.get(`/graph/company/${encodeURIComponent(company)}/recruiters`),
};

// Decision Engine
export const decisionsApi = {
  getLog: (limit = 50) => api.get('/decisions/log', { params: { limit } }),
  getStats: () => api.get('/decisions/stats'),
  evaluateJob: (jobId: string, userId: string) =>
    api.post(`/decisions/evaluate/${jobId}`, null, { params: { user_id: userId } }),
  batchEvaluate: (userId: string, limit = 50) =>
    api.post('/decisions/batch-evaluate', null, { params: { user_id: userId, limit } }),
};

// Predictive AI
export const predictionsApi = {
  getTrends: () => api.get('/predictions/trends'),
  getCompany: (name: string) => api.get(`/predictions/company/${encodeURIComponent(name)}`),
  getOpportunities: () => api.get('/predictions/opportunities'),
  getStats: () => api.get('/predictions/stats'),
};

// LinkedIn Automation
export const linkedinApi = {
  connect: (data: any) => api.post('/linkedin/connect', data),
  bulkConnect: (connections: any[]) => api.post('/linkedin/bulk-connect', { connections }),
  message: (data: any) => api.post('/linkedin/message', data),
  getOutreach: (status?: string) => api.get('/linkedin/outreach', { params: { status } }),
  getStats: () => api.get('/linkedin/stats'),
  markReplied: (id: string) => api.post(`/linkedin/${id}/mark-replied`),
};

// Voice AI
export const voiceApi = {
  initiateCall: (data: any) => api.post('/voice/call', data),
  getCalls: (limit = 30) => api.get('/voice/calls', { params: { limit } }),
  getCall: (id: string) => api.get(`/voice/calls/${id}`),
  getStats: () => api.get('/voice/stats'),
};

// Interview AI
export const interviewApi = {
  generatePrep: (data: any) => api.post('/interview/prep', data),
  getPreps: (limit = 20) => api.get('/interview/preps', { params: { limit } }),
  getPrep: (id: string) => api.get(`/interview/preps/${id}`),
  predictQuestions: (role: string, difficulty?: string) =>
    api.get(`/interview/questions/${encodeURIComponent(role)}`, { params: { difficulty } }),
  getStats: () => api.get('/interview/stats'),
};

// Negotiation AI
export const negotiationApi = {
  analyze: (data: any) => api.post('/negotiation/analyze', data),
  getStrategies: (limit = 20) => api.get('/negotiation/strategies', { params: { limit } }),
  getStrategy: (id: string) => api.get(`/negotiation/strategies/${id}`),
  updateStatus: (id: string, status: string) =>
    api.patch(`/negotiation/strategies/${id}`, null, { params: { status_val: status } }),
  getMarketRates: (role: string, experience?: number, location?: string, rateType?: string) =>
    api.get(`/negotiation/market-rates/${encodeURIComponent(role)}`, { params: { experience, location, rate_type: rateType } }),
  getStats: () => api.get('/negotiation/stats'),
};

// Freelance Bidding
export const freelanceApi = {
  createBid: (data: any) => api.post('/freelance/bid', data),
  submitBid: (id: string) => api.post(`/freelance/bid/${id}/submit`),
  getBids: (platform?: string, status?: string) =>
    api.get('/freelance/bids', { params: { platform, status_filter: status } }),
  getBid: (id: string) => api.get(`/freelance/bids/${id}`),
  updateBidStatus: (id: string, status: string) =>
    api.patch(`/freelance/bids/${id}`, null, { params: { new_status: status } }),
  getStats: () => api.get('/freelance/stats'),
};

// Demand Generation (Content)
export const contentApi = {
  generate: (data: any) => api.post('/content/generate', data),
  getPosts: (platform?: string, status?: string) =>
    api.get('/content/posts', { params: { platform, status_filter: status } }),
  getPost: (id: string) => api.get(`/content/posts/${id}`),
  updatePostStatus: (id: string, status: string) =>
    api.patch(`/content/posts/${id}`, null, { params: { new_status: status } }),
  updateEngagement: (id: string, data: any) => api.post(`/content/posts/${id}/engagement`, data),
  getCalendar: (days = 7) => api.get('/content/calendar', { params: { days } }),
  getStats: () => api.get('/content/stats'),
};

// Agent Orchestrator
export const agentsApi = {
  getStatus: () => api.get('/agents/status'),
  createTask: (data: any) => api.post('/agents/tasks', null, { params: data }),
  getTasks: (status?: string, agentType?: string) =>
    api.get('/agents/tasks', { params: { status_filter: status, agent_type: agentType } }),
  getTask: (id: string) => api.get(`/agents/tasks/${id}`),
  cancelTask: (id: string) => api.post(`/agents/tasks/${id}/cancel`),
  createWorkflow: (data: any) => api.post('/agents/workflows', null, { params: data }),
  getWorkflows: () => api.get('/agents/workflows'),
  runWorkflow: (id: string) => api.post(`/agents/workflows/${id}/run`),
  toggleWorkflow: (id: string, isActive: boolean) =>
    api.patch(`/agents/workflows/${id}`, null, { params: { is_active: isActive } }),
  runPipeline: () => api.post('/agents/pipeline/run'),
  getStats: () => api.get('/agents/stats'),
  // AI Planning & Execution
  createPlan: (goal: string) => api.post('/agents/plan', { goal }),
  executeTask: (taskId: string) => api.post(`/agents/tasks/${taskId}/execute`),
  getActivity: (limit = 30) => api.get('/agents/activity', { params: { limit } }),
  // MCP Tools
  getMcpTools: () => api.get('/agents/mcp/tools'),
  invokeMcpTool: (toolName: string, args: Record<string, any>) =>
    api.post('/agents/mcp/invoke', { tool_name: toolName, arguments: args }),
  getMcpCategories: () => api.get('/agents/mcp/categories'),
};

// Subscription & Billing
export const billingApi = {
  getPlans: () => api.get('/billing/plans'),
  getSubscription: () => api.get('/billing/subscription'),
  subscribe: (plan: string) => api.post('/billing/subscribe', null, { params: { plan } }),
  cancel: () => api.post('/billing/cancel'),
  getUsage: (days?: number) => api.get('/billing/usage', { params: { days } }),
  recordUsage: (actionType: string, credits?: number) =>
    api.post('/billing/usage/record', null, { params: { action_type: actionType, credits } }),
  getStats: () => api.get('/billing/stats'),
};

// Job Marketplace
export const marketplaceApi = {
  registerRecruiter: (data: any) => api.post('/marketplace/recruiter/register', null, { params: data }),
  getRecruiterProfile: () => api.get('/marketplace/recruiter/profile'),
  postJob: (data: any) => api.post('/marketplace/jobs', null, { params: data }),
  getJobs: (params?: any) => api.get('/marketplace/jobs', { params }),
  getJob: (id: string) => api.get(`/marketplace/jobs/${id}`),
  updateJobStatus: (id: string, status: string) =>
    api.patch(`/marketplace/jobs/${id}`, null, { params: { status } }),
  matchCandidates: (jobId: string) => api.post(`/marketplace/jobs/${jobId}/match`),
  getCandidates: (jobId: string) => api.get(`/marketplace/jobs/${jobId}/candidates`),
  updateCandidateStatus: (matchId: string, status: string, notes?: string) =>
    api.patch(`/marketplace/candidates/${matchId}`, null, { params: { status, recruiter_notes: notes } }),
  getStats: () => api.get('/marketplace/stats'),
};

// Recruiter Intelligence
export const recruitersApi = {
  list: (skip?: number, limit?: number) =>
    api.get('/recruiters', { params: { skip, limit } }),
  create: (data: any) => api.post('/recruiters', data),
  get: (id: string) => api.get(`/recruiters/${id}`),
  update: (id: string, data: any) => api.put(`/recruiters/${id}`, data),
  delete: (id: string) => api.delete(`/recruiters/${id}`),
  recordInteraction: (id: string, type: string, notes?: string) =>
    api.post(`/recruiters/${id}/interaction`, { interaction_type: type, notes }),
  getTopRanked: (limit?: number) =>
    api.get('/recruiters/ranking/top', { params: { limit } }),
  getStatsSummary: () => api.get('/recruiters/stats/summary'),
};

// Notification Preferences & Channels
export const notificationsApi = {
  getPreferences: () => api.get('/notifications/preferences'),
  updatePreferences: (prefs: any) => api.put('/notifications/preferences', prefs),
  setupTelegram: (chatId: string) => api.post('/notifications/setup/telegram', { chat_id: chatId }),
  setupWhatsApp: (phoneNumber: string) => api.post('/notifications/setup/whatsapp', { phone_number: phoneNumber }),
  testChannel: (channel: string) => api.post(`/notifications/test/${channel}`),
  getStats: () => api.get('/notifications/stats'),
};

// Self-Learning Feedback
export const feedbackApi = {
  submitJobFeedback: (jobId: string, feedbackType: string, notes?: string) =>
    api.post('/feedback/job', { job_id: jobId, feedback_type: feedbackType, notes }),
  getInsights: () => api.get('/feedback/insights'),
  getLearningStats: () => api.get('/feedback/learning-stats'),
};

// Webhooks (for admin/n8n integration)
export const webhooksApi = {
  getStatus: () => api.get('/webhooks/status'),
};

// Skills & Skill Profile
export const skillsApi = {
  getTaxonomy: () => api.get('/skills/taxonomy'),
  getRoleTemplates: () => api.get('/skills/role-templates'),
  generateQueries: (skills: string[], roles: string[]) =>
    api.post('/skills/generate-queries', { skills, roles }),
  getProfilePreview: () => api.get('/skills/profile-preview'),
  getSavedSearches: () => api.get('/skills/saved-searches'),
  createSavedSearch: (data: { name: string; role_categories?: string[]; skills_filter?: string[]; min_score?: number; notify_on_match?: boolean }) =>
    api.post('/skills/saved-searches', data),
  deleteSavedSearch: (id: string) => api.delete(`/skills/saved-searches/${id}`),
  toggleSavedSearch: (id: string) => api.patch(`/skills/saved-searches/${id}/toggle`),
};

// Audit Logs
export const auditApi = {
  getLogs: (params?: { limit?: number; action?: string; resource_type?: string }) =>
    api.get('/audit/logs', { params }),
  getStats: () => api.get('/audit/stats'),
};

export default api;
