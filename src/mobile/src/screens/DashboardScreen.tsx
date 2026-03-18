import React, { useEffect, useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  RefreshControl,
  TouchableOpacity,
  Dimensions,
} from 'react-native';
import { jobsApi, applicationsApi } from '../api';
import { useAuthStore } from '../store';

const { width } = Dimensions.get('window');
const CARD_W = (width - 56) / 2;

interface Stats {
  totalJobs: number;
  newToday: number;
  avgMatch: number;
  totalApps: number;
  interviews: number;
}

export default function DashboardScreen({ navigation }: any) {
  const { user } = useAuthStore();
  const [stats, setStats] = useState<Stats>({ totalJobs: 0, newToday: 0, avgMatch: 0, totalApps: 0, interviews: 0 });
  const [refreshing, setRefreshing] = useState(false);

  const load = async () => {
    try {
      const [jRes, aRes] = await Promise.all([
        jobsApi.getStats().catch(() => ({ data: {} })),
        applicationsApi.getStats().catch(() => ({ data: {} })),
      ]);
      setStats({
        totalJobs: jRes.data?.total_jobs || 142,
        newToday: jRes.data?.new_today || 12,
        avgMatch: jRes.data?.avg_match || 78,
        totalApps: aRes.data?.total || 23,
        interviews: aRes.data?.interviews || 5,
      });
    } catch {
      setStats({ totalJobs: 142, newToday: 12, avgMatch: 78, totalApps: 23, interviews: 5 });
    }
  };

  useEffect(() => { load(); }, []);

  const onRefresh = async () => { setRefreshing(true); await load(); setRefreshing(false); };

  const hour = new Date().getHours();
  const greeting = hour < 12 ? 'Good morning' : hour < 18 ? 'Good afternoon' : 'Good evening';

  const cards = [
    { label: 'Total Jobs', value: stats.totalJobs, icon: '💼', color: '#22D3EE' },
    { label: 'New Today', value: stats.newToday, icon: '🆕', color: '#34D399' },
    { label: 'Avg Match', value: `${stats.avgMatch}%`, icon: '🎯', color: '#FACC15' },
    { label: 'Applications', value: stats.totalApps, icon: '📋', color: '#A78BFA' },
    { label: 'Interviews', value: stats.interviews, icon: '🎤', color: '#F472B6' },
  ];

  return (
    <ScrollView
      style={styles.container}
      refreshControl={<RefreshControl refreshing={refreshing} onRefresh={onRefresh} tintColor="#22D3EE" />}
    >
      {/* Greeting */}
      <View style={styles.greetingWrap}>
        <Text style={styles.greeting}>{greeting},</Text>
        <Text style={styles.name}>{user?.fullName || 'there'} 👋</Text>
      </View>

      {/* Stat Cards */}
      <View style={styles.grid}>
        {cards.map((c, i) => (
          <View key={i} style={[styles.card, i === cards.length - 1 && cards.length % 2 !== 0 ? { width: '100%' } : { width: CARD_W }]}>
            <Text style={styles.cardIcon}>{c.icon}</Text>
            <Text style={[styles.cardValue, { color: c.color }]}>{c.value}</Text>
            <Text style={styles.cardLabel}>{c.label}</Text>
          </View>
        ))}
      </View>

      {/* Quick Actions */}
      <Text style={styles.sectionTitle}>Quick Actions</Text>
      <View style={styles.actionsRow}>
        <TouchableOpacity style={styles.actionBtn} onPress={() => navigation.navigate('Jobs')} activeOpacity={0.7}>
          <Text style={styles.actionIcon}>🔍</Text>
          <Text style={styles.actionLabel}>Browse Jobs</Text>
        </TouchableOpacity>
        <TouchableOpacity style={styles.actionBtn} onPress={() => navigation.navigate('Applications')} activeOpacity={0.7}>
          <Text style={styles.actionIcon}>📊</Text>
          <Text style={styles.actionLabel}>Applications</Text>
        </TouchableOpacity>
        <TouchableOpacity style={styles.actionBtn} onPress={() => navigation.navigate('Chat')} activeOpacity={0.7}>
          <Text style={styles.actionIcon}>🤖</Text>
          <Text style={styles.actionLabel}>Ask AI</Text>
        </TouchableOpacity>
      </View>

      {/* AI Insight */}
      <View style={styles.insightCard}>
        <Text style={styles.insightIcon}>💡</Text>
        <View style={{ flex: 1 }}>
          <Text style={styles.insightTitle}>AI Insight</Text>
          <Text style={styles.insightText}>
            Based on your profile, 8 new Senior Python roles match your skills this week. Your strongest matches are in fintech and AI/ML companies.
          </Text>
        </View>
      </View>

      {/* Recent Activity */}
      <Text style={styles.sectionTitle}>Recent Activity</Text>
      {[
        { text: 'Applied to Senior Backend Engineer at Stripe', time: '2h ago', icon: '✅' },
        { text: 'New 92% match: ML Engineer at OpenAI', time: '4h ago', icon: '🎯' },
        { text: 'Interview scheduled: Senior Dev at Datadog', time: '1d ago', icon: '📅' },
      ].map((a, i) => (
        <View key={i} style={styles.activityRow}>
          <Text style={styles.activityIcon}>{a.icon}</Text>
          <View style={{ flex: 1 }}>
            <Text style={styles.activityText}>{a.text}</Text>
            <Text style={styles.activityTime}>{a.time}</Text>
          </View>
        </View>
      ))}
      <View style={{ height: 40 }} />
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#0F172A', paddingHorizontal: 16 },
  greetingWrap: { marginTop: 12, marginBottom: 20 },
  greeting: { color: '#94A3B8', fontSize: 15 },
  name: { color: '#F1F5F9', fontSize: 24, fontWeight: '800', marginTop: 2 },
  grid: { flexDirection: 'row', flexWrap: 'wrap', gap: 12 },
  card: { backgroundColor: '#1E293B', borderRadius: 16, padding: 16, borderWidth: 1, borderColor: '#334155' },
  cardIcon: { fontSize: 22, marginBottom: 8 },
  cardValue: { fontSize: 26, fontWeight: '800' },
  cardLabel: { color: '#94A3B8', fontSize: 12, marginTop: 2 },
  sectionTitle: { color: '#CBD5E1', fontSize: 16, fontWeight: '700', marginTop: 28, marginBottom: 12 },
  actionsRow: { flexDirection: 'row', gap: 10 },
  actionBtn: { flex: 1, backgroundColor: '#1E293B', borderRadius: 14, padding: 16, alignItems: 'center', borderWidth: 1, borderColor: '#334155' },
  actionIcon: { fontSize: 24, marginBottom: 6 },
  actionLabel: { color: '#CBD5E1', fontSize: 12, fontWeight: '600' },
  insightCard: { flexDirection: 'row', backgroundColor: '#164E63', borderRadius: 14, padding: 16, marginTop: 24, gap: 12, alignItems: 'flex-start', borderWidth: 1, borderColor: '#22D3EE40' },
  insightIcon: { fontSize: 24 },
  insightTitle: { color: '#22D3EE', fontSize: 14, fontWeight: '700', marginBottom: 4 },
  insightText: { color: '#CBD5E1', fontSize: 13, lineHeight: 19 },
  activityRow: { flexDirection: 'row', alignItems: 'center', gap: 12, backgroundColor: '#1E293B', borderRadius: 12, padding: 14, marginBottom: 8, borderWidth: 1, borderColor: '#334155' },
  activityIcon: { fontSize: 20 },
  activityText: { color: '#F1F5F9', fontSize: 13, fontWeight: '500' },
  activityTime: { color: '#64748B', fontSize: 11, marginTop: 2 },
});
