import axios from "axios";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export const api = axios.create({
  baseURL: API_URL,
  headers: { "Content-Type": "application/json" },
});

// Attach JWT token to every request
api.interceptors.request.use((config) => {
  if (typeof window !== "undefined") {
    const token = localStorage.getItem("access_token");
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
  }
  return config;
});

// Handle 401 globally
api.interceptors.response.use(
  (res) => res,
  (err) => {
    if (err.response?.status === 401 && typeof window !== "undefined") {
      localStorage.removeItem("access_token");
      localStorage.removeItem("user");
      window.location.href = "/auth/login";
    }
    return Promise.reject(err);
  }
);

// ── Auth ──────────────────────────────────────────────────────────────────────
export const authApi = {
  signup: (data: { full_name: string; email: string; password: string; workspace_name: string }) =>
    api.post("/api/auth/signup", data),
  login: (email: string, password: string) => {
    const formData = new URLSearchParams();
    formData.append("username", email);
    formData.append("password", password);
    return api.post("/api/auth/login", formData, {
      headers: { "Content-Type": "application/x-www-form-urlencoded" },
    });
  },
  me: () => api.get("/api/auth/me"),
};

// ── Leads ────────────────────────────────────────────────────────────────────
export const leadsApi = {
  list: (params?: Record<string, unknown>) => api.get("/api/leads", { params }),
  get: (id: string) => api.get(`/api/leads/${id}`),
  create: (data: Record<string, unknown>) => api.post("/api/leads", data),
  update: (id: string, data: Record<string, unknown>) => api.patch(`/api/leads/${id}`, data),
  delete: (id: string) => api.delete(`/api/leads/${id}`),
  reAnalyze: (id: string) => api.post(`/api/leads/${id}/re-analyze`),
};

// ── Campaigns ────────────────────────────────────────────────────────────────
export const campaignsApi = {
  list: () => api.get("/api/campaigns"),
  get: (id: string) => api.get(`/api/campaigns/${id}`),
  create: (data: Record<string, unknown>) => api.post("/api/campaigns", data),
  update: (id: string, data: Record<string, unknown>) => api.patch(`/api/campaigns/${id}`, data),
  delete: (id: string) => api.delete(`/api/campaigns/${id}`),
};

// ── Automations ───────────────────────────────────────────────────────────────
export const automationsApi = {
  list: () => api.get("/api/automations"),
  create: (data: Record<string, unknown>) => api.post("/api/automations", data),
  update: (id: string, data: Record<string, unknown>) => api.patch(`/api/automations/${id}`, data),
  delete: (id: string) => api.delete(`/api/automations/${id}`),
  seedDefaults: () => api.post("/api/automations/seed-defaults"),
  getLogs: (id: string) => api.get(`/api/automations/${id}/logs`),
};

// ── Conversations ─────────────────────────────────────────────────────────────
export const conversationsApi = {
  getByLead: (leadId: string) => api.get(`/api/conversations/lead/${leadId}`),
  getMessages: (convId: string) => api.get(`/api/conversations/${convId}/messages`),
  send: (convId: string, data: Record<string, unknown>) =>
    api.post(`/api/conversations/${convId}/send`, data),
  start: (leadId: string, channel?: string) =>
    api.post(`/api/conversations/lead/${leadId}/start`, null, { params: { channel } }),
};

// ── Analytics ─────────────────────────────────────────────────────────────────
export const analyticsApi = {
  dashboard: (days?: number) => api.get("/api/analytics/dashboard", { params: { days } }),
  insights: () => api.get("/api/analytics/ai-insights"),
  campaignRoi: () => api.get("/api/analytics/campaigns/roi"),
};

// ── Billing ───────────────────────────────────────────────────────────────────
export const billingApi = {
  plans: () => api.get("/api/billing/plans"),
  subscription: () => api.get("/api/billing/subscription"),
  checkout: (plan: string, success_url: string, cancel_url: string) =>
    api.post("/api/billing/checkout", { plan, success_url, cancel_url }),
  portal: (return_url: string) =>
    api.post("/api/billing/portal", null, { params: { return_url } }),
};
