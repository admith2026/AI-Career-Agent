'use client';

import { useState, useRef, useEffect } from 'react';

interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
}

const SUGGESTIONS = [
  'Show me high-paying remote Python jobs',
  'What are my best matches today?',
  'Which companies are hiring the most?',
  'Skill gap analysis for senior roles',
  'Find React Native contract jobs',
  'Summarize my application status',
];

export default function AIChatAssistant() {
  const [open, setOpen] = useState(false);
  const [messages, setMessages] = useState<Message[]>([
    {
      id: '0',
      role: 'assistant',
      content: "Hello! I'm your AI Career Assistant. Ask me about jobs, applications, skill gaps, or anything career-related. Try a suggestion below or type your own question.",
      timestamp: new Date(),
    },
  ]);
  const [input, setInput] = useState('');
  const [typing, setTyping] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, typing]);

  useEffect(() => {
    if (open) inputRef.current?.focus();
  }, [open]);

  const generateResponse = (query: string): string => {
    const q = query.toLowerCase();
    if (q.includes('remote') && q.includes('python'))
      return "I found 12 remote Python positions with match scores above 80%. Top matches:\n\n• **Senior Python Developer** at TechCorp (92% match, $150-180k)\n• **Python Backend Engineer** at DataFlow Inc (88% match, $140-170k)\n• **ML Python Engineer** at AI Labs (85% match, $160-200k)\n\nWould you like me to auto-apply to the top matches?";
    if (q.includes('best match') || q.includes('top match'))
      return "Your top 5 matches today:\n\n1. **Staff Engineer** — Stripe (95% match)\n2. **Senior Backend Developer** — Figma (91% match)\n3. **Platform Engineer** — Vercel (89% match)\n4. **Python Lead** — DataDog (87% match)\n5. **Full-Stack Engineer** — Linear (85% match)\n\nAll are remote-friendly and within your salary range.";
    if (q.includes('company') || q.includes('hiring'))
      return "Companies with the most active hiring signals:\n\n🏢 **Stripe** — 23 open roles, Series I\n🏢 **Vercel** — 18 roles, just raised $150M\n🏢 **Figma** — 15 roles, expanding platform team\n🏢 **Linear** — 12 roles, growing fast\n\nWant me to prioritize jobs from any of these?";
    if (q.includes('skill gap') || q.includes('skill'))
      return "Based on your profile vs. top job requirements:\n\n✅ **Strong**: Python, React, PostgreSQL, Docker\n⚠️ **Moderate**: Kubernetes, GraphQL, Redis\n❌ **Gap**: Rust, Go, Terraform\n\n**Recommendation**: Learning Kubernetes and Terraform could increase your match score by ~15% across senior roles. I can find courses for you.";
    if (q.includes('react native') || q.includes('mobile'))
      return "I found 8 React Native contract positions:\n\n• **React Native Developer** — FinTech startup ($80-100/hr)\n• **Mobile Engineer** — HealthTech ($90-120/hr)\n• **Senior RN Developer** — E-commerce ($85-110/hr)\n\nAll are 6+ month contracts. Want me to generate tailored resumes?";
    if (q.includes('application') || q.includes('status'))
      return "Your application pipeline:\n\n📋 **Pending**: 3 applications\n✅ **Applied**: 8 applications\n🎯 **Interview**: 2 scheduled\n💰 **Offered**: 1 offer\n❌ **Rejected**: 2\n\nYou have an interview with Stripe tomorrow at 2PM. Should I help you prepare?";
    return "I can help you with:\n\n• **Job search** — Find jobs by skill, location, salary\n• **Match analysis** — See why a job matches your profile\n• **Skill gaps** — Identify areas to improve\n• **Applications** — Track and manage applications\n• **Company intel** — Research hiring companies\n\nWhat would you like to know?";
  };

  const handleSend = (text?: string) => {
    const msg = text || input.trim();
    if (!msg) return;

    const userMsg: Message = {
      id: Date.now().toString(),
      role: 'user',
      content: msg,
      timestamp: new Date(),
    };
    setMessages((prev) => [...prev, userMsg]);
    setInput('');
    setTyping(true);

    setTimeout(() => {
      const response = generateResponse(msg);
      const assistantMsg: Message = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: response,
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, assistantMsg]);
      setTyping(false);
    }, 800 + Math.random() * 700);
  };

  const showSuggestions = messages.length <= 1;

  return (
    <>
      {/* Chat Toggle Button */}
      <button
        onClick={() => setOpen(!open)}
        className={`fixed bottom-6 right-6 z-50 w-14 h-14 rounded-2xl flex items-center justify-center transition-all duration-300 shadow-lg ${
          open
            ? 'bg-navy-800 border border-gray-700/50 rotate-0'
            : 'bg-gradient-to-br from-cyan-400 to-cyan-600 shadow-glow hover:scale-105'
        }`}
      >
        {open ? (
          <svg className="w-6 h-6 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
          </svg>
        ) : (
          <svg className="w-6 h-6 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z" />
          </svg>
        )}
      </button>

      {/* Chat Panel */}
      {open && (
        <div className="fixed bottom-24 right-6 z-50 w-[400px] max-h-[600px] flex flex-col bg-navy-900 border border-gray-700/40 rounded-2xl shadow-2xl animate-slide-up overflow-hidden">
          {/* Header */}
          <div className="p-4 border-b border-gray-700/30 bg-navy-900/80 backdrop-blur-sm">
            <div className="flex items-center gap-3">
              <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-cyan-400 to-blue-500 flex items-center justify-center shadow-glow">
                <svg className="w-5 h-5 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
                </svg>
              </div>
              <div>
                <h3 className="text-sm font-semibold text-white">AI Career Assistant</h3>
                <div className="flex items-center gap-1.5">
                  <span className="w-2 h-2 rounded-full bg-green-400 animate-pulse" />
                  <span className="text-[11px] text-gray-500">Online · Powered by AI</span>
                </div>
              </div>
            </div>
          </div>

          {/* Messages */}
          <div className="flex-1 overflow-y-auto p-4 space-y-4 min-h-[300px] max-h-[400px]">
            {messages.map((msg) => (
              <div key={msg.id} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                <div
                  className={`max-w-[85%] rounded-2xl px-4 py-2.5 text-sm leading-relaxed ${
                    msg.role === 'user'
                      ? 'bg-cyan-500/20 text-cyan-100 rounded-br-md'
                      : 'bg-navy-800 text-gray-300 rounded-bl-md border border-gray-700/30'
                  }`}
                >
                  <div className="whitespace-pre-wrap">{msg.content.split(/(\*\*.*?\*\*)/).map((part, i) => {
                    if (part.startsWith('**') && part.endsWith('**')) {
                      return <strong key={i} className="text-white font-semibold">{part.slice(2, -2)}</strong>;
                    }
                    return <span key={i}>{part}</span>;
                  })}</div>
                  <p className="text-[10px] text-gray-600 mt-1">
                    {msg.timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                  </p>
                </div>
              </div>
            ))}
            {typing && (
              <div className="flex justify-start">
                <div className="bg-navy-800 border border-gray-700/30 rounded-2xl rounded-bl-md px-4 py-3">
                  <div className="flex gap-1.5">
                    <span className="w-2 h-2 bg-gray-500 rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
                    <span className="w-2 h-2 bg-gray-500 rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
                    <span className="w-2 h-2 bg-gray-500 rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
                  </div>
                </div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>

          {/* Suggestions */}
          {showSuggestions && (
            <div className="px-4 pb-2">
              <p className="text-[10px] text-gray-500 uppercase tracking-wider mb-2">Suggestions</p>
              <div className="flex flex-wrap gap-1.5">
                {SUGGESTIONS.map((s) => (
                  <button
                    key={s}
                    onClick={() => handleSend(s)}
                    className="text-[11px] px-2.5 py-1 rounded-lg bg-navy-800 text-gray-400 border border-gray-700/30 hover:border-cyan-400/30 hover:text-cyan-400 transition-all"
                  >
                    {s}
                  </button>
                ))}
              </div>
            </div>
          )}

          {/* Input */}
          <div className="p-3 border-t border-gray-700/30 bg-navy-900/80 backdrop-blur-sm">
            <div className="flex items-center gap-2">
              <input
                ref={inputRef}
                type="text"
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && handleSend()}
                placeholder="Ask about jobs, skills, companies..."
                className="flex-1 bg-navy-800 border border-gray-700/40 rounded-xl px-4 py-2.5 text-sm text-white placeholder-gray-500 focus:outline-none focus:border-cyan-400/40 transition-colors"
              />
              <button
                onClick={() => handleSend()}
                disabled={!input.trim() || typing}
                className="w-10 h-10 rounded-xl bg-gradient-to-r from-cyan-400 to-cyan-600 flex items-center justify-center text-white disabled:opacity-30 hover:shadow-glow transition-all flex-shrink-0"
              >
                <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
                </svg>
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  );
}
