import axios from 'axios'

const baseURL = import.meta.env.VITE_API_BASE_URL || '/'
const routerBase = import.meta.env.VITE_ROUTER_BASENAME || (import.meta.env.PROD ? '/dashboard' : '')
const loginPath = `${routerBase}/login`.replace(/\/{2,}/g, '/')

const api = axios.create({ baseURL })

api.interceptors.request.use(cfg => {
  const token = localStorage.getItem('etherius_token')
  if (token) cfg.headers.Authorization = `Bearer ${token}`
  return cfg
})

api.interceptors.response.use(r => r, err => {
  const status = err.response?.status
  const detail = String(err.response?.data?.detail || '').toLowerCase()
  const subscriptionBlocked = status === 403 && detail.includes('subscription')
  if (status === 401 || subscriptionBlocked) {
    localStorage.removeItem('etherius_token')
    localStorage.removeItem('etherius_user')
    window.location.href = loginPath
  }
  return Promise.reject(err)
})

export const authAPI = {
  login: (email, password) => api.post('/api/auth/login', { email, password }),
  register: (data) => api.post('/api/auth/register', data),
  me: () => api.get('/api/auth/me'),
  createUser: (data) => api.post('/api/auth/users', data),
  listUsers: () => api.get('/api/auth/users'),
}

export const dashboardAPI = {
  stats: () => api.get('/api/dashboard/stats'),
  alerts: (params) => api.get('/api/dashboard/alerts', { params }),
  updateAlert: (id, data) => api.patch(`/api/dashboard/alerts/${id}`, data),
  endpoints: () => api.get('/api/dashboard/endpoints'),
  endpointEvents: (id) => api.get(`/api/dashboard/endpoints/${id}/events`),
  loginActivity: (params) => api.get('/api/dashboard/login-activity', { params }),
  blockedIPs: () => api.get('/api/dashboard/blocked-ips'),
  auditLogs: () => api.get('/api/dashboard/audit-logs'),
}

export const responseAPI = {
  blockIP: (ip, reason) => api.post('/api/response/block-ip', { ip_address: ip, reason }),
  unblockIP: (id) => api.delete(`/api/response/unblock-ip/${id}`),
  isolate: (endpoint_id, reason) => api.post('/api/response/isolate', { endpoint_id, reason }),
  unisolate: (endpoint_id) => api.post('/api/response/unisolate', { endpoint_id }),
}

export const agentAPI = {
  register: (data) => api.post('/api/agent/register', data),
}

export const licenseAPI = {
  subscription: () => api.get('/api/licenses/subscription'),
  createEmployeeKey: (data) => api.post('/api/licenses/employee', data),
  listEmployeeKeys: () => api.get('/api/licenses/employee'),
  revokeEmployeeKey: (id) => api.patch(`/api/licenses/employee/${id}/revoke`),
}
