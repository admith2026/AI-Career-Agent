import React, { useEffect } from 'react';
import { NavigationContainer, DefaultTheme } from '@react-navigation/native';
import { createBottomTabNavigator } from '@react-navigation/bottom-tabs';
import { StatusBar } from 'expo-status-bar';
import { View, Text, ActivityIndicator, StyleSheet } from 'react-native';
import { useAuthStore } from './src/store';
import LoginScreen from './src/screens/LoginScreen';
import JobsScreen from './src/screens/JobsScreen';
import ApplicationsScreen from './src/screens/ApplicationsScreen';
import DashboardScreen from './src/screens/DashboardScreen';
import ChatScreen from './src/screens/ChatScreen';
import ProfileScreen from './src/screens/ProfileScreen';

const Tab = createBottomTabNavigator();

const DarkTheme = {
  ...DefaultTheme,
  colors: {
    ...DefaultTheme.colors,
    primary: '#22D3EE',
    background: '#0F172A',
    card: '#1E293B',
    text: '#f9fafb',
    border: '#334155',
  },
};

function TabIcon({ label, focused }: { label: string; focused: boolean }) {
  const icons: Record<string, string> = {
    Home: '🏠',
    Jobs: '💼',
    Applications: '📋',
    Chat: '🤖',
    Profile: '👤',
  };
  return (
    <View style={{ alignItems: 'center', paddingTop: 4 }}>
      <Text style={{ fontSize: 20 }}>{icons[label] || '📌'}</Text>
      <Text style={{ color: focused ? '#22D3EE' : '#64748B', fontSize: 9, marginTop: 2, fontWeight: focused ? '600' : '400' }}>
        {label}
      </Text>
    </View>
  );
}

export default function App() {
  const { token, isLoading, loadSession } = useAuthStore();

  useEffect(() => { loadSession(); }, []);

  if (isLoading) {
    return (
      <View style={styles.center}>
        <ActivityIndicator size="large" color="#22D3EE" />
      </View>
    );
  }

  if (!token) {
    return (
      <>
        <StatusBar style="light" />
        <LoginScreen />
      </>
    );
  }

  return (
    <>
      <StatusBar style="light" />
      <NavigationContainer theme={DarkTheme}>
        <Tab.Navigator
          screenOptions={({ route }) => ({
            tabBarIcon: ({ focused }) => <TabIcon label={route.name} focused={focused} />,
            tabBarShowLabel: false,
            headerStyle: { backgroundColor: '#0F172A', elevation: 0, shadowOpacity: 0 },
            headerTintColor: '#f9fafb',
            headerTitleStyle: { fontWeight: '700' },
            tabBarStyle: { backgroundColor: '#0F172A', borderTopColor: '#1E293B', borderTopWidth: 1, height: 64, paddingBottom: 6 },
          })}
        >
          <Tab.Screen name="Home" component={DashboardScreen} options={{ headerTitle: 'Dashboard' }} />
          <Tab.Screen name="Jobs" component={JobsScreen} />
          <Tab.Screen name="Applications" component={ApplicationsScreen} />
          <Tab.Screen name="Chat" component={ChatScreen} options={{ headerTitle: 'AI Assistant' }} />
          <Tab.Screen name="Profile" component={ProfileScreen} />
        </Tab.Navigator>
      </NavigationContainer>
    </>
  );
}

const styles = StyleSheet.create({
  center: { flex: 1, justifyContent: 'center', alignItems: 'center', backgroundColor: '#0F172A' },
});
