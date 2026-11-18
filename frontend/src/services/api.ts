import axios from 'axios';
import type { User } from '../types';

const API_BASE = import.meta.env.VITE_API_URL || '/api/v1';

export const apiClient = axios.create({
  baseURL: API_BASE,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor to attach JWT
apiClient.interceptors.request.use((config) => {
  const token = localStorage.getItem('verisight_access_token');
  if (token && config.headers) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Response interceptor for automatic refresh
apiClient.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;
      const refreshToken = localStorage.getItem('verisight_refresh_token');
      if (refreshToken) {
        try {
          const res = await axios.post(`${API_BASE}/auth/refresh`, { refresh_token: refreshToken });
          localStorage.setItem('verisight_access_token', res.data.access_token);
          localStorage.setItem('verisight_refresh_token', res.data.refresh_token);
          originalRequest.headers.Authorization = `Bearer ${res.data.access_token}`;
          return apiClient(originalRequest);
        } catch (refreshErr) {
          localStorage.removeItem('verisight_access_token');
          localStorage.removeItem('verisight_refresh_token');
          localStorage.removeItem('verisight_user');
          window.location.href = '/login';
        }
      }
    }
    return Promise.reject(error);
  }
);

// Auth endpoints
export const authApi = {
  login: async (credentials: { email: string; password: string }) => {
    const res = await apiClient.post('/auth/login', credentials);
    return res.data;
  },
  refresh: async (refreshToken: string) => {
    const res = await apiClient.post('/auth/refresh', { refresh_token: refreshToken });
    return res.data;
  },
  logout: async () => {
    try {
      await apiClient.post('/auth/logout');
    } finally {
      localStorage.removeItem('verisight_access_token');
      localStorage.removeItem('verisight_refresh_token');
      localStorage.removeItem('verisight_user');
    }
  },
  getMe: async (): Promise<User> => {
    const res = await apiClient.get('/auth/me');
    return res.data;
  },
  resetPassword: async (email: string) => {
    const res = await apiClient.post('/auth/reset-password', { email });
    return res.data;
  },
  confirmReset: async (data: { token: string; new_password: string }) => {
    const res = await apiClient.post('/auth/confirm-reset', data);
    return res.data;
  },
};

// Screenings & Processing endpoints
export const screeningsApi = {
  create: async (formData: FormData) => {
    const res = await apiClient.post('/screenings', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
    return res.data;
  },
  list: async (params?: { skip?: number; limit?: number; status_filter?: string; risk_filter?: string }) => {
    const res = await apiClient.get('/screenings', { params });
    return res.data;
  },
  get: async (id: string) => {
    const res = await apiClient.get(`/screenings/${id}`);
    return res.data;
  },
  getDocumentUrl: (id: string, processed: boolean = false) => {
    const token = localStorage.getItem('verisight_access_token');
    return `/api/v1/screenings/${id}/document?processed=${processed}&token=${token || ''}`;
  },
  getQuality: async (id: string) => {
    const res = await apiClient.get(`/screenings/${id}/quality`);
    return res.data;
  },
  getFields: async (id: string) => {
    const res = await apiClient.get(`/screenings/${id}/fields`);
    return res.data;
  },
  correctField: async (screeningId: string, fieldId: string, data: { new_value: string; notes?: string }) => {
    const res = await apiClient.patch(`/screenings/${screeningId}/fields/${fieldId}`, data);
    return res.data;
  },
  getMRZ: async (id: string) => {
    const res = await apiClient.get(`/screenings/${id}/mrz`);
    return res.data;
  },
  getStatus: async (id: string) => {
    const res = await apiClient.get(`/screenings/${id}/status`);
    return res.data;
  },
  retry: async (id: string) => {
    const res = await apiClient.post(`/screenings/${id}/retry`);
    return res.data;
  },
  cancel: async (id: string) => {
    const res = await apiClient.post(`/screenings/${id}/cancel`);
    return res.data;
  },
};

// Forensics endpoints
export const forensicsApi = {
  getFindings: async (screeningId: string) => {
    const res = await apiClient.get(`/forensics/${screeningId}`);
    return res.data;
  },
  getHeatmapUrl: (screeningId: string) => {
    return `/api/v1/forensics/${screeningId}/heatmap`;
  },
};

// Risk Assessment endpoints
export const riskApi = {
  getAssessment: async (screeningId: string) => {
    const res = await apiClient.get(`/risk/${screeningId}`);
    return res.data;
  },
  overrideRisk: async (screeningId: string, data: { override_level: string; reason: string }) => {
    const res = await apiClient.post(`/risk/${screeningId}/override`, data);
    return res.data;
  },
};

// Face Verification endpoints
export const faceApi = {
  getPortrait: async (screeningId: string) => {
    const res = await apiClient.get(`/face/${screeningId}/portrait`);
    return res.data;
  },
  verify: async (screeningId: string, formData: FormData) => {
    const res = await apiClient.post(`/face/${screeningId}/verify`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
    return res.data;
  },
};

// Cases endpoints
export const casesApi = {
  list: async (params?: { status?: string; priority?: string }) => {
    const res = await apiClient.get('/cases', { params });
    return res.data;
  },
  get: async (id: string) => {
    const res = await apiClient.get(`/cases/${id}`);
    return res.data;
  },
  create: async (data: { screening_id: string; priority?: string; summary?: string }) => {
    const res = await apiClient.post('/cases', data);
    return res.data;
  },
  updateStatus: async (id: string, data: { status: string; priority?: string; resolution_notes?: string; notes?: string }) => {
    const res = await apiClient.patch(`/cases/${id}/status`, data);
    return res.data;
  },
  addNote: async (id: string, text: string) => {
    const res = await apiClient.post(`/cases/${id}/notes`, { text });
    return res.data;
  },
};

// Institutional Report endpoints
export const reportsApi = {
  getDownloadUrl: (screeningId: string) => `${API_BASE}/reports/${screeningId}/download`,
  download: async (screeningId: string, filename?: string) => {
    const res = await apiClient.get(`/reports/${screeningId}/download`, {
      responseType: 'blob',
    });
    const url = window.URL.createObjectURL(new Blob([res.data], { type: 'application/pdf' }));
    const link = document.createElement('a');
    link.href = url;
    link.setAttribute('download', filename || `VERISIGHT_DOSSIER_${screeningId}.pdf`);
    document.body.appendChild(link);
    link.click();
    link.remove();
    window.URL.revokeObjectURL(url);
  },
};

// Audit chain endpoints
export const auditApi = {
  list: async (params?: { skip?: number; limit?: number }) => {
    const res = await apiClient.get('/audit', { params });
    return res.data;
  },
  verifyIntegrity: async () => {
    const res = await apiClient.get('/audit/verify-integrity');
    return res.data;
  },
};

// Dashboard endpoints
export const dashboardApi = {
  getStats: async () => {
    const res = await apiClient.get('/dashboard/stats');
    return res.data;
  },
};

// Standalone Quick Check endpoints
export const quickCheckApi = {
  upload: async (file: File) => {
    const formData = new FormData();
    formData.append('file', file);
    const res = await apiClient.post('/quick-checks', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
    return res.data;
  },
  get: async (checkId: string) => {
    const res = await apiClient.get(`/quick-checks/${checkId}`);
    return res.data;
  },
  escalate: async (checkId: string) => {
    const res = await apiClient.post(`/quick-checks/${checkId}/escalate`);
    return res.data;
  },
};
