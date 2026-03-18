import React, { useEffect, useState } from 'react';
import {
  View,
  Text,
  FlatList,
  StyleSheet,
  TouchableOpacity,
  Linking,
} from 'react-native';
import { applicationsApi } from '../api';

interface Application {
  id: string;
  status: string;
  applied_via: string | null;
  applied_at: string | null;
  created_at: string | null;
  job?: {
    job_title: string;
    company_name: string | null;
    source: string;
    job_link: string;
  } | null;
}

export default function ApplicationsScreen() {
  const [apps, setApps] = useState<Application[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    (async () => {
      try {
        const res = await applicationsApi.list();
        setApps(res.data);
      } catch {
        setApps([]);
      } finally {
        setLoading(false);
      }
    })();
  }, []);

  const statusColors: Record<string, string> = {
    pending: '#FACC15',
    applied: '#22D3EE',
    interview: '#A78BFA',
    offered: '#34D399',
    rejected: '#F87171',
  };

  const renderApp = ({ item }: { item: Application }) => (
    <View style={styles.card}>
      <View style={styles.row}>
        <View style={{ flex: 1 }}>
          <Text style={styles.title}>{item.job?.job_title || 'Unknown'}</Text>
          <Text style={styles.company}>
            {item.job?.company_name || ''} · {item.job?.source || ''}
          </Text>
        </View>
        <View style={[styles.badge, { backgroundColor: (statusColors[item.status] || '#6b7280') + '20' }]}>
          <Text style={[styles.badgeText, { color: statusColors[item.status] || '#6b7280' }]}>
            {item.status}
          </Text>
        </View>
      </View>
      <Text style={styles.date}>
        {item.applied_at ? `Applied ${new Date(item.applied_at).toLocaleDateString()}` : 'Pending'}
      </Text>
      {item.job?.job_link && (
        <TouchableOpacity onPress={() => Linking.openURL(item.job!.job_link)}>
          <Text style={styles.link}>View Job →</Text>
        </TouchableOpacity>
      )}
    </View>
  );

  if (loading) {
    return <View style={styles.center}><Text style={styles.muted}>Loading...</Text></View>;
  }

  return (
    <FlatList
      data={apps}
      keyExtractor={(item) => item.id}
      renderItem={renderApp}
      contentContainerStyle={styles.list}
      ListEmptyComponent={<View style={styles.center}><Text style={styles.muted}>No applications yet.</Text></View>}
    />
  );
}

const styles = StyleSheet.create({
  list: { padding: 16, backgroundColor: '#0F172A' },
  center: { flex: 1, justifyContent: 'center', alignItems: 'center', backgroundColor: '#0F172A' },
  muted: { color: '#64748B', fontSize: 14 },
  card: { backgroundColor: '#1E293B', borderRadius: 16, padding: 16, marginBottom: 12, borderWidth: 1, borderColor: '#334155' },
  row: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'flex-start' },
  title: { color: '#F1F5F9', fontSize: 15, fontWeight: '700' },
  company: { color: '#94A3B8', fontSize: 13, marginTop: 2 },
  badge: { borderRadius: 10, paddingHorizontal: 12, paddingVertical: 5 },
  badgeText: { fontSize: 11, fontWeight: '800', textTransform: 'capitalize' },
  date: { color: '#64748B', fontSize: 12, marginTop: 8 },
  link: { color: '#22D3EE', fontSize: 13, marginTop: 6, fontWeight: '600' },
});
