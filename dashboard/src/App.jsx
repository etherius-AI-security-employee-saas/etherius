import { useEffect, useState } from 'react'
import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom'
import { AuthProvider, useAuth } from './context/AuthContext'
import { buildCompanyWebSocket, dashboardAPI } from './api/client'
import Sidebar from './components/Sidebar'
import Login from './pages/Login'
import Dashboard from './pages/Dashboard'
import Alerts from './pages/Alerts'
import Endpoints from './pages/Endpoints'
import Incidents from './pages/Incidents'
import BlockedIPs from './pages/BlockedIPs'
import AuditLog from './pages/AuditLog'
import Settings from './pages/Settings'
import USBControl from './pages/USBControl'
import AppControl from './pages/AppControl'
import WebControl from './pages/WebControl'
import InsiderThreats from './pages/InsiderThreats'
import Vulnerabilities from './pages/Vulnerabilities'
import Reports from './pages/Reports'

const routerBasename = import.meta.env.VITE_ROUTER_BASENAME || '/'

function Layout() {
  const { user, loading } = useAuth()
  const canUsePrivilegedOps = ['admin', 'superadmin'].includes(user?.role)
  const isCustomerManager = user?.role === 'manager'
  const canManageEmployees = ['manager', 'admin', 'superadmin'].includes(user?.role)
  const [liveAlertCount, setLiveAlertCount] = useState(0)
  const [toast, setToast] = useState(null)

  useEffect(() => {
    if (!user?.company_id) return
    dashboardAPI.stats().then(r => setLiveAlertCount(r.data?.open_alerts || 0)).catch(() => {})
  }, [user?.company_id])

  useEffect(() => {
    if (!user?.company_id) return undefined
    const wsUrl = buildCompanyWebSocket(user.company_id)
    if (!wsUrl) return undefined
    let socket = null
    try {
      socket = new WebSocket(wsUrl)
      socket.onmessage = event => {
        try {
          const payload = JSON.parse(event.data)
          if (payload?.type === 'alert_created') {
            setLiveAlertCount(prev => prev + 1)
            setToast({
              id: String(Date.now()),
              severity: payload.severity,
              text: `${payload.severity?.toUpperCase() || 'ALERT'}: ${payload.event_type} on endpoint`,
            })
            if (payload.severity === 'critical' && localStorage.getItem('etherius_sound_alert') === 'true') {
              const audioCtx = new (window.AudioContext || window.webkitAudioContext)()
              const osc = audioCtx.createOscillator()
              const gain = audioCtx.createGain()
              osc.type = 'sine'
              osc.frequency.value = 880
              gain.gain.value = 0.04
              osc.connect(gain)
              gain.connect(audioCtx.destination)
              osc.start()
              osc.stop(audioCtx.currentTime + 0.15)
            }
          }
        } catch {}
      }
    } catch {}
    return () => {
      try { socket?.close() } catch {}
    }
  }, [user?.company_id])

  useEffect(() => {
    if (!toast) return undefined
    const timer = setTimeout(() => setToast(null), 3500)
    return () => clearTimeout(timer)
  }, [toast])

  if (loading) {
    return (
      <div style={{
        minHeight: '100vh',
        display: 'grid',
        placeItems: 'center',
        padding: 24,
      }}>
        <div className="panel" style={{ padding: 28, width: 'min(420px, 100%)', textAlign: 'center' }}>
          <div style={{
            width: 58,
            height: 58,
            margin: '0 auto 18px',
            borderRadius: 18,
            background: 'linear-gradient(135deg, #0070f3, #0058cc 55%, #49a3ff)',
            boxShadow: '0 16px 32px rgba(0, 112, 243, 0.34)',
            display: 'grid',
            placeItems: 'center',
          }}>
            <div style={{
              width: 24,
              height: 24,
              borderRadius: '50%',
              border: '2px solid rgba(255,255,255,0.3)',
              borderTopColor: 'white',
              animation: 'spin 0.8s linear infinite',
            }} />
          </div>
          <style>{'@keyframes spin{to{transform:rotate(360deg)}}'}</style>
          <div style={{ fontSize: 18, fontWeight: 700 }}>Starting Etherius</div>
          <div style={{ color: 'var(--muted)', marginTop: 8 }}>Loading your security workspace and verifying your session.</div>
        </div>
      </div>
    )
  }

  if (!user) return <Navigate to="/login" replace />

  return (
    <div className="app-shell">
      <Sidebar liveAlertCount={liveAlertCount} />
      <main className="app-main">
        <Routes>
          <Route index element={<Dashboard />} />
          <Route path="/alerts" element={<Alerts />} />
          <Route path="/endpoints" element={<Endpoints />} />
          <Route path="/usb-control" element={canManageEmployees ? <USBControl /> : <Navigate to="/" replace />} />
          <Route path="/app-control" element={canManageEmployees ? <AppControl /> : <Navigate to="/" replace />} />
          <Route path="/web-control" element={canManageEmployees ? <WebControl /> : <Navigate to="/" replace />} />
          <Route path="/insider-threats" element={canManageEmployees ? <InsiderThreats /> : <Navigate to="/" replace />} />
          <Route path="/vulnerabilities" element={canManageEmployees ? <Vulnerabilities /> : <Navigate to="/" replace />} />
          <Route path="/reports" element={canManageEmployees ? <Reports /> : <Navigate to="/" replace />} />
          <Route path="/employee-access" element={isCustomerManager ? <Settings /> : <Navigate to="/" replace />} />
          <Route path="/incidents" element={canUsePrivilegedOps ? <Incidents /> : <Navigate to="/" replace />} />
          <Route path="/blocked" element={canUsePrivilegedOps ? <BlockedIPs /> : <Navigate to="/" replace />} />
          <Route path="/audit" element={canUsePrivilegedOps ? <AuditLog /> : <Navigate to="/" replace />} />
          <Route path="/settings" element={canUsePrivilegedOps ? <Settings /> : <Navigate to="/" replace />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
        {toast ? (
          <div style={{ position: 'fixed', right: 24, top: 24, zIndex: 1200 }}>
            <div className="panel" style={{ padding: '12px 14px', borderColor: toast.severity === 'critical' ? 'rgba(255, 71, 87, 0.42)' : 'rgba(0, 112, 243, 0.35)' }}>
              <div style={{ fontWeight: 700, fontSize: 12, color: toast.severity === 'critical' ? '#ff4757' : '#0070f3' }}>New Alert</div>
              <div style={{ marginTop: 4, color: 'var(--muted)', fontSize: 12 }}>{toast.text}</div>
            </div>
          </div>
        ) : null}
      </main>
    </div>
  )
}

export default function App() {
  return (
    <AuthProvider>
      <BrowserRouter basename={routerBasename}>
        <Routes>
          <Route path="/login" element={<Login />} />
          <Route path="/*" element={<Layout />} />
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  )
}
