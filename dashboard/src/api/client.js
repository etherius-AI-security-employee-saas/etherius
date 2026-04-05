import axios from 'axios'

const baseURL = import.meta.env.VITE_API_BASE_URL || '/'
const routerBase = import.meta.env.VITE_ROUTER_BASENAME || ''
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
  events: (params) => api.get('/api/dashboard/events', { params }),
  loginActivity: (params) => api.get('/api/dashboard/login-activity', { params }),
  blockedIPs: () => api.get('/api/dashboard/blocked-ips'),
  auditLogs: () => api.get('/api/dashboard/audit-logs'),
  usbPolicy: () => api.get('/api/dashboard/usb-policy'),
  setUsbPolicy: (policy) => api.post('/api/dashboard/usb-policy', { policy }),
  usbWhitelist: () => api.get('/api/dashboard/usb-whitelist'),
  upsertUsbWhitelist: (payload) => api.post('/api/dashboard/usb-whitelist', payload),
  appBlacklist: () => api.get('/api/dashboard/app-blacklist'),
  addAppBlacklist: (payload) => api.post('/api/dashboard/app-blacklist', payload),
  removeAppBlacklist: (id) => api.delete(`/api/dashboard/app-blacklist/${id}`),
  blockedDomains: () => api.get('/api/dashboard/blocked-domains'),
  addBlockedDomain: (payload) => api.post('/api/dashboard/blocked-domains', payload),
  removeBlockedDomain: (id) => api.delete(`/api/dashboard/blocked-domains/${id}`),
  insiderScores: (params) => api.get('/api/dashboard/insider-scores', { params }),
  vulnerabilities: () => api.get('/api/dashboard/vulnerabilities'),
  commandHistory: (params) => api.get('/api/dashboard/command-history', { params }),
  reportSummary: (params) => api.get('/api/dashboard/reports/security-summary', { params }),
  reportPdf: (params) => api.get('/api/dashboard/reports/export-pdf', { params, responseType: 'blob' }),
}

export const responseAPI = {
  blockIP: (ip, reason) => api.post('/api/response/block-ip', { ip_address: ip, reason }),
  unblockIP: (id) => api.delete(`/api/response/unblock-ip/${id}`),
  isolate: (endpoint_id, reason) => api.post('/api/response/isolate', { endpoint_id, reason }),
  unisolate: (endpoint_id) => api.post('/api/response/unisolate', { endpoint_id }),
  lockScreen: (endpoint_id) => api.post('/api/response/lock-screen', { endpoint_id }),
  remoteMessage: (endpoint_id, message) => api.post('/api/response/remote-message', { endpoint_id, message }),
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

export function buildCompanyWebSocket(companyId) {
  const token = localStorage.getItem('etherius_token')
  if (!token || !companyId) return null
  const envBase = import.meta.env.VITE_API_BASE_URL || window.location.origin
  const normalized = envBase.endsWith('/') ? envBase.slice(0, -1) : envBase
  const wsBase = normalized.replace(/^http/, 'ws')
  return `${wsBase}/ws/${companyId}?token=${encodeURIComponent(token)}`
}
