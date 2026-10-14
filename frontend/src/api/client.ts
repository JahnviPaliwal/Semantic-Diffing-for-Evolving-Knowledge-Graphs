import axios, { AxiosError } from 'axios';
import {
  DiffResponse,
  EvalBenchmark,
  Job,
  Project,
  TemporalGraphResponse,
  TokenResponse,
  User,
} from './types';

const API_BASE = (import.meta as any).env?.VITE_API_URL || '/api/v1';

export const apiClient = axios.create({
  baseURL: API_BASE,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Ephemeral in-memory Groq API Key (never saved to localStorage/sessionStorage/DB)
let ephemeralGroqApiKey: string = '';

export const setSessionGroqApiKey = (key: string): void => {
  ephemeralGroqApiKey = (key || '').trim();
};

export const getSessionGroqApiKey = (): string => {
  return ephemeralGroqApiKey;
};

// Interceptor to inject Bearer access token and ephemeral X-Groq-Api-Key header
apiClient.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token');
  if (token && config.headers) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  if (ephemeralGroqApiKey && config.headers) {
    config.headers['X-Groq-Api-Key'] = ephemeralGroqApiKey;
  }
  return config;
});

// Interceptor for 401 auto-refresh
apiClient.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    const originalRequest: any = error.config;
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;
      const refreshToken = localStorage.getItem('refresh_token');
      if (refreshToken) {
        try {
          const res = await axios.post<TokenResponse>(`${API_BASE}/auth/refresh`, {
            refresh_token: refreshToken,
          });
          localStorage.setItem('access_token', res.data.access_token);
          localStorage.setItem('refresh_token', res.data.refresh_token);
          originalRequest.headers.Authorization = `Bearer ${res.data.access_token}`;
          return apiClient(originalRequest);
        } catch (refreshErr) {
          localStorage.removeItem('access_token');
          localStorage.removeItem('refresh_token');
          localStorage.removeItem('user');
        }
      }
    }
    return Promise.reject(error);
  }
);

export const authApi = {
  login: async (email: string, password: string): Promise<TokenResponse> => {
    const res = await apiClient.post<TokenResponse>('/auth/login', { email, password });
    return res.data;
  },
  register: async (email: string, password: string): Promise<TokenResponse> => {
    const res = await apiClient.post<TokenResponse>('/auth/register', { email, password });
    return res.data;
  },
  me: async (): Promise<User> => {
    const res = await apiClient.get<User>('/auth/me');
    return res.data;
  },
};

export const projectsApi = {
  list: async (): Promise<Project[]> => {
    const res = await apiClient.get<Project[]>('/projects');
    return res.data;
  },
  get: async (id: number): Promise<Project> => {
    const res = await apiClient.get<Project>(`/projects/${id}`);
    return res.data;
  },
  create: async (name: string, description?: string): Promise<Project> => {
    const res = await apiClient.post<Project>('/projects', { name, description });
    return res.data;
  },
  update: async (id: number, name?: string, description?: string): Promise<Project> => {
    const res = await apiClient.put<Project>(`/projects/${id}`, { name, description });
    return res.data;
  },
  delete: async (id: number): Promise<{ ok: boolean }> => {
    const res = await apiClient.delete<{ ok: boolean }>(`/projects/${id}`);
    return res.data;
  },
  getTimeline: async (id: number): Promise<TemporalGraphResponse> => {
    const res = await apiClient.get<TemporalGraphResponse>(`/projects/${id}/timeline`);
    return res.data;
  },
};

export const versionsApi = {
  upload: async (projectId: number, file: File): Promise<{ job_id: string; message: string }> => {
    const formData = new FormData();
    formData.append('file', file);
    const res = await apiClient.post<{ job_id: string; message: string }>(
      `/projects/${projectId}/versions`,
      formData,
      {
        headers: { 'Content-Type': 'multipart/form-data' },
      }
    );
    return res.data;
  },
};

export const diffApi = {
  compute: async (projectId: number, fromVersionId: number, toVersionId: number): Promise<DiffResponse> => {
    const res = await apiClient.post<DiffResponse>(`/projects/${projectId}/diff`, {
      from_version_id: fromVersionId,
      to_version_id: toVersionId,
    });
    return res.data;
  },
  get: async (projectId: number, diffId: number): Promise<DiffResponse> => {
    const res = await apiClient.get<DiffResponse>(`/projects/${projectId}/diff/${diffId}`);
    return res.data;
  },
  exportUrl: (projectId: number, diffId: number, format: 'json' | 'csv'): string => {
    return `${API_BASE}/projects/${projectId}/diff/${diffId}/export?format=${format}`;
  },
};

export const jobsApi = {
  get: async (jobId: string): Promise<Job> => {
    const res = await apiClient.get<Job>(`/jobs/${jobId}`);
    return res.data;
  },
};

export const evalApi = {
  getLatest: async (): Promise<EvalBenchmark> => {
    const res = await apiClient.get<EvalBenchmark>('/eval/latest');
    return res.data;
  },
  run: async (): Promise<EvalBenchmark> => {
    const res = await apiClient.post<EvalBenchmark>('/eval/run');
    return res.data;
  },
};
