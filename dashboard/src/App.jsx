import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom'
import { AuthProvider, useAuth } from './context/AuthContext'
import Sidebar from './components/Sidebar'
import Login from './pages/Login'
import Dashboard from './pages/Dashboard'
import Alerts from './pages/Alerts'
import Endpoints from './pages/Endpoints'
import Incidents from './pages/Incidents'
import BlockedIPs from './pages/BlockedIPs'
import AuditLog from './pages/AuditLog'
import Settings from './pages/Settings'

const routerBasename = import.meta.env.VITE_ROUTER_BASENAME || (import.meta.env.PROD ? '/dashboard' : '/')

function Layout() {
  const { user, loading } = useAuth()
  const canUsePrivilegedOps = ['admin', 'superadmin'].includes(user?.role)

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
            background: 'linear-gradient(135deg, #1f8fff, #00c9b8)',
            boxShadow: '0 16px 32px rgba(21, 118, 217, 0.28)',
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
      <Sidebar />
      <main className="app-main">
        <Routes>
          <Route index element={<Dashboard />} />
          <Route path="/alerts" element={<Alerts />} />
          <Route path="/endpoints" element={<Endpoints />} />
          <Route path="/incidents" element={canUsePrivilegedOps ? <Incidents /> : <Navigate to="/" replace />} />
          <Route path="/blocked" element={canUsePrivilegedOps ? <BlockedIPs /> : <Navigate to="/" replace />} />
          <Route path="/audit" element={canUsePrivilegedOps ? <AuditLog /> : <Navigate to="/" replace />} />
          <Route path="/settings" element={<Settings />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
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
