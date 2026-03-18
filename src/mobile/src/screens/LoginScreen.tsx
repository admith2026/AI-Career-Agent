import React, { useState } from 'react';
import {
  View,
  Text,
  TextInput,
  TouchableOpacity,
  StyleSheet,
  Alert,
  ActivityIndicator,
  KeyboardAvoidingView,
  Platform,
} from 'react-native';
import { authApi } from '../api';
import { useAuthStore } from '../store';

export default function LoginScreen() {
  const { setAuth } = useAuthStore();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [fullName, setFullName] = useState('');
  const [isRegister, setIsRegister] = useState(false);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async () => {
    if (!email || !password) { Alert.alert('Error', 'Email and password required'); return; }
    setLoading(true);
    try {
      const res = isRegister
        ? await authApi.register(email, fullName, password)
        : await authApi.login(email, password);
      const { token, user } = res.data;
      await setAuth(token, { id: user.id, email: user.email, fullName: user.full_name });
    } catch (err: any) {
      Alert.alert('Error', err.response?.data?.detail || 'Authentication failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <KeyboardAvoidingView style={styles.container} behavior={Platform.OS === 'ios' ? 'padding' : undefined}>
      {/* Logo */}
      <View style={styles.logoWrap}>
        <View style={styles.logoCircle}>
          <Text style={styles.logoEmoji}>🤖</Text>
        </View>
        <Text style={styles.title}>AI Career Agent</Text>
        <Text style={styles.tagline}>Your autonomous job search companion</Text>
      </View>

      <Text style={styles.heading}>
        {isRegister ? 'Create Account' : 'Welcome Back'}
      </Text>

      {isRegister && (
        <TextInput
          style={styles.input}
          placeholder="Full Name"
          placeholderTextColor="#64748B"
          value={fullName}
          onChangeText={setFullName}
        />
      )}
      <TextInput
        style={styles.input}
        placeholder="Email"
        placeholderTextColor="#64748B"
        value={email}
        onChangeText={setEmail}
        keyboardType="email-address"
        autoCapitalize="none"
      />
      <TextInput
        style={styles.input}
        placeholder="Password"
        placeholderTextColor="#64748B"
        value={password}
        onChangeText={setPassword}
        secureTextEntry
      />

      <TouchableOpacity style={styles.button} onPress={handleSubmit} disabled={loading} activeOpacity={0.8}>
        {loading ? (
          <ActivityIndicator color="#0F172A" />
        ) : (
          <Text style={styles.buttonText}>
            {isRegister ? 'Create Account' : 'Sign In'}
          </Text>
        )}
      </TouchableOpacity>

      <TouchableOpacity onPress={() => setIsRegister(!isRegister)}>
        <Text style={styles.linkText}>
          {isRegister ? 'Already have an account? Sign In' : "Don't have an account? Register"}
        </Text>
      </TouchableOpacity>
    </KeyboardAvoidingView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    justifyContent: 'center',
    paddingHorizontal: 24,
    backgroundColor: '#0F172A',
  },
  logoWrap: { alignItems: 'center', marginBottom: 28 },
  logoCircle: { width: 72, height: 72, borderRadius: 36, backgroundColor: '#164E63', alignItems: 'center', justifyContent: 'center', marginBottom: 12 },
  logoEmoji: { fontSize: 36 },
  title: {
    fontSize: 26,
    fontWeight: '800',
    color: '#22D3EE',
    textAlign: 'center',
    letterSpacing: 0.5,
  },
  tagline: {
    fontSize: 13,
    color: '#64748B',
    textAlign: 'center',
    marginTop: 4,
  },
  heading: {
    fontSize: 20,
    fontWeight: '700',
    color: '#F1F5F9',
    textAlign: 'center',
    marginBottom: 20,
  },
  input: {
    backgroundColor: '#1E293B',
    borderWidth: 1,
    borderColor: '#334155',
    borderRadius: 12,
    padding: 15,
    color: '#F1F5F9',
    marginBottom: 12,
    fontSize: 15,
  },
  button: {
    backgroundColor: '#22D3EE',
    borderRadius: 12,
    padding: 16,
    alignItems: 'center',
    marginTop: 8,
    marginBottom: 16,
  },
  buttonText: {
    color: '#0F172A',
    fontWeight: '700',
    fontSize: 16,
  },
  linkText: {
    color: '#22D3EE',
    textAlign: 'center',
    fontSize: 13,
  },
});
