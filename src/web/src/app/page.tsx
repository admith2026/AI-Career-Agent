'use client';

import { useState, useEffect } from 'react';
import Sidebar from '@/components/Sidebar';
import JobFeed from '@/components/JobFeed';
import Dashboard from '@/components/Dashboard';
import Applications from '@/components/Applications';
import ResumeManager from '@/components/ResumeManager';
import HiringSignals from '@/components/HiringSignals';
import RecruiterNetwork from '@/components/RecruiterNetwork';
import PipelineMonitor from '@/components/PipelineMonitor';
import KnowledgeGraphView from '@/components/KnowledgeGraphView';
import DecisionLog from '@/components/DecisionLog';
import AnalyticsView from '@/components/AnalyticsView';
import SkillGapAnalysis from '@/components/SkillGapAnalysis';
import SkillProfileSetup from '@/components/SkillProfileSetup';
import PredictionsView from '@/components/PredictionsView';
import LinkedInOutreach from '@/components/LinkedInOutreach';
import VoiceCalls from '@/components/VoiceCalls';
import InterviewPrepView from '@/components/InterviewPrepView';
import NegotiationView from '@/components/NegotiationView';
import FreelanceBids from '@/components/FreelanceBids';
import DemandGeneration from '@/components/DemandGeneration';
import AgentOrchestratorView from '@/components/AgentOrchestratorView';
import SubscriptionView from '@/components/SubscriptionView';
import MarketplaceView from '@/components/MarketplaceView';
import LoginForm from '@/components/LoginForm';
import AIChatAssistant from '@/components/AIChatAssistant';
import NotificationPanel, { NotificationBell } from '@/components/NotificationPanel';
import { useAuthStore } from '@/lib/store';

type View = 'dashboard' | 'jobs' | 'applications' | 'resumes' | 'signals' | 'recruiters' | 'pipeline' | 'graph' | 'decisions' | 'analytics' | 'skills' | 'skill-profile' | 'predictions' | 'linkedin' | 'voice' | 'interview' | 'negotiation' | 'freelance' | 'content' | 'agents' | 'subscription' | 'marketplace';

export default function Home() {
  const { token } = useAuthStore();
  const [currentView, setCurrentView] = useState<View>('dashboard');
  const [mounted, setMounted] = useState(false);
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const [notificationsOpen, setNotificationsOpen] = useState(false);

  useEffect(() => setMounted(true), []);

  if (!mounted) return null;

  if (!token) {
    return <LoginForm />;
  }

  const renderView = () => {
    switch (currentView) {
      case 'dashboard': return <Dashboard onNavigate={setCurrentView} />;
      case 'jobs': return <JobFeed />;
      case 'applications': return <Applications />;
      case 'resumes': return <ResumeManager />;
      case 'signals': return <HiringSignals />;
      case 'recruiters': return <RecruiterNetwork />;
      case 'pipeline': return <PipelineMonitor />;
      case 'graph': return <KnowledgeGraphView />;
      case 'decisions': return <DecisionLog />;
      case 'analytics': return <AnalyticsView />;
      case 'skills': return <SkillGapAnalysis />;
      case 'skill-profile': return <SkillProfileSetup />;
      case 'predictions': return <PredictionsView />;
      case 'linkedin': return <LinkedInOutreach />;
      case 'voice': return <VoiceCalls />;
      case 'interview': return <InterviewPrepView />;
      case 'negotiation': return <NegotiationView />;
      case 'freelance': return <FreelanceBids />;
      case 'content': return <DemandGeneration />;
      case 'agents': return <AgentOrchestratorView />;
      case 'subscription': return <SubscriptionView />;
      case 'marketplace': return <MarketplaceView />;
      default: return <Dashboard onNavigate={setCurrentView} />;
    }
  };

  return (
    <div className="flex h-screen bg-navy-950">
      <Sidebar
        currentView={currentView}
        onNavigate={setCurrentView}
        collapsed={sidebarCollapsed}
        onToggle={() => setSidebarCollapsed(!sidebarCollapsed)}
      />
      <main className="flex-1 overflow-auto relative">
        {/* Top bar with notifications */}
        <div className="sticky top-0 z-30 flex items-center justify-end px-6 lg:px-8 pt-4 pb-2">
          <NotificationBell count={3} onClick={() => setNotificationsOpen(!notificationsOpen)} />
        </div>
        <div className="px-6 lg:px-8 pb-8 max-w-[1600px] mx-auto">
          {renderView()}
        </div>
      </main>

      {/* Overlays */}
      <NotificationPanel open={notificationsOpen} onClose={() => setNotificationsOpen(false)} />
      <AIChatAssistant />
    </div>
  );
}
