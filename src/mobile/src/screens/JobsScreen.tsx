import React, { useEffect, useState, useCallback } from 'react';
import {
  View,
  Text,
  FlatList,
  TouchableOpacity,
  StyleSheet,
  RefreshControl,
  Linking,
  Alert,
} from 'react-native';
import { jobsApi, applicationsApi } from '../api';

interface Job {
  id: string;
  job_title: string;
  company_name: string | null;
  source: string;
  location: string | null;
  salary_or_rate: string | null;
  job_link: string;
  analysis?: { match_score: number; technologies: string[] } | null;
}

export default function JobsScreen() {
  const [jobs, setJobs] = useState<Job[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [page, setPage] = useState(1);

  const fetchJobs = useCallback(async (p = 1) => {
    try {
      const res = await jobsApi.getJobs(p);
      if (p === 1) {
        setJobs(res.data.data);
      } else {
        setJobs((prev) => [...prev, ...res.data.data]);
      }
    } catch {
      // silent
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, []);

  useEffect(() => { fetchJobs(); }, [fetchJobs]);

  const onRefresh = () => {
    setRefreshing(true);
    setPage(1);
    fetchJobs(1);
  };

  const onEndReached = () => {
    const next = page + 1;
    setPage(next);
    fetchJobs(next);
  };

  const handleApply = async (jobId: string) => {
    try {
      await applicationsApi.apply(jobId);
      Alert.alert('Success', 'Application submitted!');
    } catch (err: any) {
      Alert.alert('Error', err.response?.data?.detail || 'Failed to apply');
    }
  };

  const renderJob = ({ item }: { item: Job }) => (
    <View style={styles.card}>
      <View style={styles.cardHeader}>
        <Text style={styles.title} numberOfLines={2}>{item.job_title}</Text>
        {item.analysis?.match_score != null && (
          <View style={[styles.scoreBadge, { backgroundColor: item.analysis.match_score >= 70 ? '#164E63' : '#854d0e20' }]}>
            <Text style={[styles.scoreText, { color: item.analysis.match_score >= 70 ? '#22D3EE' : '#FACC15' }]}>
              {item.analysis.match_score}
            </Text>
          </View>
        )}
      </View>
      <Text style={styles.company}>
        {item.company_name || 'Unknown'} · {item.source}
      </Text>
      {item.salary_or_rate ? <Text style={styles.salary}>{item.salary_or_rate}</Text> : null}
      {item.analysis?.technologies && item.analysis.technologies.length > 0 && (
        <View style={styles.techRow}>
          {item.analysis.technologies.slice(0, 4).map((t) => (
            <View key={t} style={styles.techBadge}>
              <Text style={styles.techText}>{t}</Text>
            </View>
          ))}
        </View>
      )}
      <View style={styles.actions}>
        <TouchableOpacity style={styles.viewBtn} onPress={() => Linking.openURL(item.job_link)}>
          <Text style={styles.viewBtnText}>View</Text>
        </TouchableOpacity>
        <TouchableOpacity style={styles.applyBtn} onPress={() => handleApply(item.id)}>
          <Text style={styles.applyBtnText}>Apply</Text>
        </TouchableOpacity>
      </View>
    </View>
  );

  if (loading) {
    return <View style={styles.center}><Text style={styles.muted}>Loading jobs...</Text></View>;
  }

  return (
    <FlatList
      data={jobs}
      keyExtractor={(item) => item.id}
      renderItem={renderJob}
      contentContainerStyle={styles.list}
      refreshControl={<RefreshControl refreshing={refreshing} onRefresh={onRefresh} tintColor="#22D3EE" />}
      onEndReached={onEndReached}
      onEndReachedThreshold={0.3}
      ListEmptyComponent={<View style={styles.center}><Text style={styles.muted}>No jobs found.</Text></View>}
    />
  );
}

const styles = StyleSheet.create({
  list: { padding: 16, backgroundColor: '#0F172A' },
  center: { flex: 1, justifyContent: 'center', alignItems: 'center', backgroundColor: '#0F172A' },
  muted: { color: '#64748B', fontSize: 14 },
  card: { backgroundColor: '#1E293B', borderRadius: 16, padding: 16, marginBottom: 12, borderWidth: 1, borderColor: '#334155' },
  cardHeader: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'flex-start' },
  title: { color: '#F1F5F9', fontSize: 16, fontWeight: '700', flex: 1 },
  scoreBadge: { borderRadius: 12, paddingHorizontal: 10, paddingVertical: 5, marginLeft: 8 },
  scoreText: { fontSize: 13, fontWeight: '800' },
  company: { color: '#94A3B8', fontSize: 13, marginTop: 4 },
  salary: { color: '#34D399', fontSize: 13, marginTop: 4, fontWeight: '600' },
  techRow: { flexDirection: 'row', flexWrap: 'wrap', marginTop: 10, gap: 6 },
  techBadge: { backgroundColor: '#164E63', borderRadius: 8, paddingHorizontal: 10, paddingVertical: 4, borderWidth: 1, borderColor: '#22D3EE30' },
  techText: { color: '#22D3EE', fontSize: 11, fontWeight: '500' },
  actions: { flexDirection: 'row', marginTop: 14, gap: 10 },
  viewBtn: { backgroundColor: '#334155', borderRadius: 10, paddingHorizontal: 18, paddingVertical: 10, flex: 1, alignItems: 'center' },
  viewBtnText: { color: '#CBD5E1', fontSize: 13, fontWeight: '600' },
  applyBtn: { backgroundColor: '#22D3EE', borderRadius: 10, paddingHorizontal: 18, paddingVertical: 10, flex: 1, alignItems: 'center' },
  applyBtnText: { color: '#0F172A', fontSize: 13, fontWeight: '700' },
});
