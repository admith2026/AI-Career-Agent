import React, { useState, useRef, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TextInput,
  TouchableOpacity,
  FlatList,
  KeyboardAvoidingView,
  Platform,
  Animated,
} from 'react-native';

interface Message {
  id: string;
  role: 'user' | 'assistant';
  text: string;
  time: string;
}

const SUGGESTIONS = [
  'Find remote Python jobs',
  'Best matching roles for me',
  'Companies hiring this week',
  'Skill gaps to work on',
  'Application status update',
  'Interview prep tips',
];

const MOCK_RESPONSES: Record<string, string> = {
  remote: "I found 12 remote Python positions this week. Top matches:\n\n• Senior Python Dev at Stripe (91% match)\n• Backend Engineer at GitLab (88% match)\n• ML Platform Eng at Datadog (85% match)\n\nWould you like details on any of these?",
  match: "Your top 3 matching roles right now:\n\n1. 🎯 Senior Python Dev — Stripe (91%)\n2. 🎯 Backend Engineer — GitLab (88%)\n3. 🎯 ML Platform Eng — Datadog (85%)\n\nYour strongest match areas are Python, system design, and cloud.",
  company: "Companies actively hiring in your domain:\n\n• Stripe — 3 open positions\n• OpenAI — 2 positions (ML focus)\n• Datadog — 4 positions\n• GitLab — 2 remote positions\n\nAll have > 80% match with your profile.",
  skill: "Based on market demand, here are skill gaps to focus on:\n\n📈 High priority: Kubernetes, Rust\n📊 Medium: GraphQL, Terraform\n✅ Strong: Python, React, PostgreSQL\n\nI recommend starting with Kubernetes — it appears in 67% of your matched jobs.",
  status: "Your application status summary:\n\n✅ Applied: 23 total\n📞 Interview: 5 (2 this week)\n⏳ Pending: 8 awaiting response\n❌ Rejected: 4\n\nYou have an interview with Datadog on Thursday!",
  interview: "Here are some tips for your upcoming interviews:\n\n1. Review system design patterns\n2. Practice coding problems on LeetCode\n3. Prepare STAR method stories\n4. Research each company's tech stack\n\nWant me to create a prep plan for a specific company?",
};

function getResponse(text: string): string {
  const lower = text.toLowerCase();
  if (lower.includes('remote') || lower.includes('python')) return MOCK_RESPONSES.remote;
  if (lower.includes('match') || lower.includes('best')) return MOCK_RESPONSES.match;
  if (lower.includes('company') || lower.includes('hiring')) return MOCK_RESPONSES.company;
  if (lower.includes('skill') || lower.includes('gap')) return MOCK_RESPONSES.skill;
  if (lower.includes('status') || lower.includes('application')) return MOCK_RESPONSES.status;
  if (lower.includes('interview') || lower.includes('prep')) return MOCK_RESPONSES.interview;
  return "I can help you with job searching, skill analysis, and application tracking. Try asking about:\n\n• Remote jobs in your field\n• Your best matching roles\n• Skill gaps to work on\n• Application status updates";
}

function now() {
  return new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
}

export default function ChatScreen() {
  const [messages, setMessages] = useState<Message[]>([
    { id: '0', role: 'assistant', text: "Hi! I'm your AI Career Assistant. Ask me about jobs, skills, applications, or interview prep. How can I help?", time: now() },
  ]);
  const [input, setInput] = useState('');
  const [typing, setTyping] = useState(false);
  const flatRef = useRef<FlatList>(null);
  const dotAnim = useRef(new Animated.Value(0)).current;

  useEffect(() => {
    if (typing) {
      Animated.loop(
        Animated.sequence([
          Animated.timing(dotAnim, { toValue: 1, duration: 500, useNativeDriver: true }),
          Animated.timing(dotAnim, { toValue: 0, duration: 500, useNativeDriver: true }),
        ])
      ).start();
    } else {
      dotAnim.stopAnimation();
    }
  }, [typing]);

  const send = (text: string) => {
    if (!text.trim()) return;
    const userMsg: Message = { id: Date.now().toString(), role: 'user', text: text.trim(), time: now() };
    setMessages(prev => [...prev, userMsg]);
    setInput('');
    setTyping(true);

    setTimeout(() => {
      const resp: Message = { id: (Date.now() + 1).toString(), role: 'assistant', text: getResponse(text), time: now() };
      setMessages(prev => [...prev, resp]);
      setTyping(false);
    }, 1200);
  };

  const renderMessage = ({ item }: { item: Message }) => (
    <View style={[styles.bubble, item.role === 'user' ? styles.userBubble : styles.aiBubble]}>
      {item.role === 'assistant' && <Text style={styles.aiLabel}>🤖 AI Assistant</Text>}
      <Text style={styles.msgText}>{item.text}</Text>
      <Text style={styles.time}>{item.time}</Text>
    </View>
  );

  return (
    <KeyboardAvoidingView style={styles.container} behavior={Platform.OS === 'ios' ? 'padding' : undefined} keyboardVerticalOffset={90}>
      <FlatList
        ref={flatRef}
        data={messages}
        keyExtractor={m => m.id}
        renderItem={renderMessage}
        contentContainerStyle={styles.list}
        onContentSizeChange={() => flatRef.current?.scrollToEnd({ animated: true })}
        ListHeaderComponent={
          messages.length <= 1 ? (
            <View style={styles.suggestWrap}>
              <Text style={styles.suggestTitle}>Suggested questions</Text>
              <View style={styles.suggestGrid}>
                {SUGGESTIONS.map((s, i) => (
                  <TouchableOpacity key={i} style={styles.suggestBtn} onPress={() => send(s)} activeOpacity={0.7}>
                    <Text style={styles.suggestText}>{s}</Text>
                  </TouchableOpacity>
                ))}
              </View>
            </View>
          ) : null
        }
        ListFooterComponent={
          typing ? (
            <View style={[styles.bubble, styles.aiBubble, { paddingVertical: 14 }]}>
              <Animated.Text style={[styles.dots, { opacity: dotAnim }]}>● ● ●</Animated.Text>
            </View>
          ) : null
        }
      />

      {/* Input */}
      <View style={styles.inputRow}>
        <TextInput
          style={styles.input}
          value={input}
          onChangeText={setInput}
          placeholder="Ask me anything..."
          placeholderTextColor="#64748B"
          onSubmitEditing={() => send(input)}
          returnKeyType="send"
        />
        <TouchableOpacity style={[styles.sendBtn, !input.trim() && { opacity: 0.4 }]} onPress={() => send(input)} disabled={!input.trim()} activeOpacity={0.7}>
          <Text style={styles.sendIcon}>➤</Text>
        </TouchableOpacity>
      </View>
    </KeyboardAvoidingView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#0F172A' },
  list: { padding: 16, paddingBottom: 8 },
  bubble: { borderRadius: 16, padding: 14, marginBottom: 10, maxWidth: '85%' },
  userBubble: { backgroundColor: '#164E63', alignSelf: 'flex-end', borderBottomRightRadius: 4 },
  aiBubble: { backgroundColor: '#1E293B', alignSelf: 'flex-start', borderBottomLeftRadius: 4, borderWidth: 1, borderColor: '#334155' },
  aiLabel: { color: '#22D3EE', fontSize: 11, fontWeight: '700', marginBottom: 6 },
  msgText: { color: '#F1F5F9', fontSize: 14, lineHeight: 21 },
  time: { color: '#64748B', fontSize: 10, marginTop: 6, textAlign: 'right' },
  dots: { color: '#22D3EE', fontSize: 16, textAlign: 'center' },
  inputRow: { flexDirection: 'row', padding: 12, gap: 8, borderTopWidth: 1, borderTopColor: '#1E293B', backgroundColor: '#0F172A' },
  input: { flex: 1, backgroundColor: '#1E293B', borderRadius: 24, paddingHorizontal: 18, paddingVertical: 12, color: '#F1F5F9', fontSize: 15, borderWidth: 1, borderColor: '#334155' },
  sendBtn: { width: 48, height: 48, borderRadius: 24, backgroundColor: '#22D3EE', alignItems: 'center', justifyContent: 'center' },
  sendIcon: { color: '#0F172A', fontSize: 20, fontWeight: '700' },
  suggestWrap: { marginBottom: 16 },
  suggestTitle: { color: '#94A3B8', fontSize: 13, fontWeight: '600', marginBottom: 10 },
  suggestGrid: { flexDirection: 'row', flexWrap: 'wrap', gap: 8 },
  suggestBtn: { backgroundColor: '#1E293B', borderRadius: 20, paddingHorizontal: 14, paddingVertical: 10, borderWidth: 1, borderColor: '#22D3EE30' },
  suggestText: { color: '#22D3EE', fontSize: 13 },
});
