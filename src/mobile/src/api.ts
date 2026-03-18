import axios from 'axios';
import AsyncStorage from '@react-native-async-storage/async-storage';

const API_BASE = 'http://localhost:5000/api';

const api = axios.create({
  baseURL: API_BASE,
  headers: { 'Content-Type': 'application/json' },
});

api.interceptors.request.use(async (config) => {
  const token = await AsyncStorage.getItem('token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

export const authApi = {
  login: (email: string, password: string) =>
    api.post('/auth/login', { email, password }),
  register: (email: string, fullName: string, password: string) =>
    api.post('/auth/register', { email, full_name: fullName, password }),
};

export const jobsApi = {
  getJobs: (page = 1, pageSize = 20) =>
    api.get('/jobs', { params: { page, page_size: pageSize } }),
  getJob: (id: string) => api.get(`/jobs/${id}`),
  getStats: () => api.get('/jobs/stats'),
};

export const applicationsApi = {
  apply: (jobId: string) => api.post('/applications', { job_id: jobId }),
  list: (page = 1) => api.get('/applications', { params: { page } }),
  getStats: () => api.get('/applications/stats'),
};

export const profileApi = {
  getProfile: () => api.get('/profile'),
  updateProfile: (data: any) => api.put('/profile', data),
};

export default api;
