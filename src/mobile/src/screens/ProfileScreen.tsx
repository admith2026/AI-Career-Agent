import React from 'react';
import { View, Text, StyleSheet, ScrollView, TouchableOpacity, Alert } from 'react-native';
import { useAuthStore } from '../store';

export default function ProfileScreen() {
  const { user, logout } = useAuthStore();

  const skills = ['Python', 'React', 'TypeScript', 'PostgreSQL', 'Docker', 'AWS', 'FastAPI', 'Redis'];
  const profileStats = [
    { label: 'Profile Score', value: '87%', color: '#22D3EE' },
    { label: 'Skills Listed', value: String(skills.length), color: '#34D399' },
    { label: 'Job Alerts', value: 'Active', color: '#FACC15' },
  ];

  const handleSignOut = () => {
    Alert.alert('Sign Out', 'Are you sure?', [
      { text: 'Cancel', style: 'cancel' },
      { text: 'Sign Out', style: 'destructive', onPress: logout },
    ]);
  };

  return (
    <ScrollView style={styles.container}>
      {/* Header */}
      <View style={styles.header}>
        <View style={styles.avatar}>
          <Text style={styles.avatarText}>{(user?.fullName || 'U').charAt(0).toUpperCase()}</Text>
        </View>
        <Text style={styles.name}>{user?.fullName || 'User'}</Text>
        <Text style={styles.email}>{user?.email || ''}</Text>
      </View>

      {/* Stats */}
      <View style={styles.statsRow}>
        {profileStats.map((s, i) => (
          <View key={i} style={styles.statCard}>
            <Text style={[styles.statValue, { color: s.color }]}>{s.value}</Text>
            <Text style={styles.statLabel}>{s.label}</Text>
          </View>
        ))}
      </View>

      {/* Skills */}
      <Text style={styles.sectionTitle}>Your Skills</Text>
      <View style={styles.skillsWrap}>
        {skills.map((s, i) => (
          <View key={i} style={styles.skillBadge}>
            <Text style={styles.skillText}>{s}</Text>
          </View>
        ))}
      </View>

      {/* Preferences */}
      <Text style={styles.sectionTitle}>Preferences</Text>
      {[
        { icon: '📍', label: 'Location', value: 'Remote / San Francisco' },
        { icon: '💰', label: 'Salary Range', value: '$150k - $220k' },
        { icon: '🏢', label: 'Company Size', value: 'Mid to Large' },
        { icon: '📊', label: 'Role Level', value: 'Senior / Staff' },
      ].map((p, i) => (
        <View key={i} style={styles.prefRow}>
          <Text style={styles.prefIcon}>{p.icon}</Text>
          <View style={{ flex: 1 }}>
            <Text style={styles.prefLabel}>{p.label}</Text>
            <Text style={styles.prefValue}>{p.value}</Text>
          </View>
        </View>
      ))}

      {/* Sign Out */}
      <TouchableOpacity style={styles.signOutBtn} onPress={handleSignOut} activeOpacity={0.7}>
        <Text style={styles.signOutText}>Sign Out</Text>
      </TouchableOpacity>

      <View style={{ height: 40 }} />
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#0F172A', paddingHorizontal: 16 },
  header: { alignItems: 'center', paddingVertical: 24 },
  avatar: { width: 80, height: 80, borderRadius: 40, backgroundColor: '#164E63', alignItems: 'center', justifyContent: 'center', marginBottom: 12, borderWidth: 2, borderColor: '#22D3EE' },
  avatarText: { color: '#22D3EE', fontSize: 32, fontWeight: '800' },
  name: { color: '#F1F5F9', fontSize: 22, fontWeight: '800' },
  email: { color: '#94A3B8', fontSize: 14, marginTop: 2 },
  statsRow: { flexDirection: 'row', gap: 10, marginTop: 8 },
  statCard: { flex: 1, backgroundColor: '#1E293B', borderRadius: 14, padding: 14, alignItems: 'center', borderWidth: 1, borderColor: '#334155' },
  statValue: { fontSize: 20, fontWeight: '800' },
  statLabel: { color: '#94A3B8', fontSize: 11, marginTop: 4 },
  sectionTitle: { color: '#CBD5E1', fontSize: 16, fontWeight: '700', marginTop: 28, marginBottom: 12 },
  skillsWrap: { flexDirection: 'row', flexWrap: 'wrap', gap: 8 },
  skillBadge: { backgroundColor: '#164E63', borderRadius: 20, paddingHorizontal: 14, paddingVertical: 8, borderWidth: 1, borderColor: '#22D3EE40' },
  skillText: { color: '#22D3EE', fontSize: 13, fontWeight: '600' },
  prefRow: { flexDirection: 'row', alignItems: 'center', gap: 12, backgroundColor: '#1E293B', borderRadius: 12, padding: 14, marginBottom: 8, borderWidth: 1, borderColor: '#334155' },
  prefIcon: { fontSize: 20 },
  prefLabel: { color: '#94A3B8', fontSize: 12 },
  prefValue: { color: '#F1F5F9', fontSize: 14, fontWeight: '600', marginTop: 2 },
  signOutBtn: { backgroundColor: '#7F1D1D', borderRadius: 12, padding: 16, alignItems: 'center', marginTop: 28, borderWidth: 1, borderColor: '#991B1B' },
  signOutText: { color: '#FCA5A5', fontSize: 15, fontWeight: '700' },
});
