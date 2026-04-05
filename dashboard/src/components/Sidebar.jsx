import { NavLink } from 'react-router-dom'
import { Activity, AlertTriangle, Ban, BarChart3, FileText, LogOut, Monitor, Settings, Shield, Usb, UserSearch, Webhook, Wrench, Zap } from 'lucide-react'
import { useAuth } from '../context/AuthContext'
import BrandMark from './BrandMark'

const NAV = [
  { to: '/', icon: BarChart3, label: 'Overview' },
  { to: '/alerts', icon: AlertTriangle, label: 'Alerts' },
  { to: '/endpoints', icon: Monitor, label: 'Endpoints' },
  { to: '/usb-control', icon: Usb, label: 'USB Control' },
  { to: '/app-control', icon: Wrench, label: 'App Control' },
  { to: '/web-control', icon: Webhook, label: 'Web Control' },
  { to: '/insider-threats', icon: UserSearch, label: 'Insider Threats' },
  { to: '/vulnerabilities', icon: Shield, label: 'Vulnerabilities' },
  { to: '/reports', icon: FileText, label: 'Reports' },
  { to: '/incidents', icon: Zap, label: 'Response' },
  { to: '/blocked', icon: Ban, label: 'Blocked IPs' },
  { to: '/audit', icon: Activity, label: 'Audit Log' },
  { to: '/settings', icon: Settings, label: 'Settings' },
]

const CUSTOMER_NAV = [
  { to: '/', icon: BarChart3, label: 'Overview' },
  { to: '/alerts', icon: AlertTriangle, label: 'Alerts' },
  { to: '/endpoints', icon: Monitor, label: 'Employees' },
  { to: '/usb-control', icon: Usb, label: 'USB Control' },
  { to: '/app-control', icon: Wrench, label: 'App Control' },
  { to: '/web-control', icon: Webhook, label: 'Web Control' },
  { to: '/insider-threats', icon: UserSearch, label: 'Insider Threats' },
  { to: '/vulnerabilities', icon: Shield, label: 'Vulnerabilities' },
  { to: '/reports', icon: FileText, label: 'Reports' },
  { to: '/employee-access', icon: Settings, label: 'Employee Access' },
]

export default function Sidebar({ liveAlertCount = 0 }) {
  const { user, logout } = useAuth()
  const navItems = user?.role === 'manager' ? CUSTOMER_NAV : NAV

  return (
    <aside style={{
      width: 246,
      minHeight: '100vh',
      background: 'linear-gradient(180deg, rgba(12, 20, 36, 0.97), rgba(7, 11, 20, 0.99))',
      borderRight: '1px solid rgba(0, 112, 243, 0.24)',
      display: 'flex',
      flexDirection: 'column',
      position: 'fixed',
      top: 0,
      left: 0,
      zIndex: 100,
      backdropFilter: 'blur(18px)',
      boxShadow: 'inset -1px 0 0 rgba(255,255,255,0.03), 16px 0 42px rgba(2, 8, 18, 0.45)',
    }}>
      <div style={{ padding: '26px 18px 18px', borderBottom: '1px solid rgba(0, 112, 243, 0.16)' }}>
        <BrandMark compact />
      </div>

      <div style={{ padding: 14 }}>
        <div className="panel" style={{ padding: 14, borderRadius: 14 }}>
          <div style={{ fontSize: 11, color: 'var(--muted)', textTransform: 'uppercase', letterSpacing: '0.12em', marginBottom: 6 }}>
            Signed In
          </div>
          <div style={{ fontSize: 14, fontWeight: 700, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
            {user?.full_name || user?.email}
          </div>
          <div style={{ color: 'var(--accent-2)', fontSize: 11, marginTop: 6, textTransform: 'uppercase', letterSpacing: '0.16em' }}>
            {user?.role}
          </div>
        </div>
      </div>

      <nav style={{ flex: 1, padding: '2px 10px 14px' }}>
        {navItems.map(({ to, icon: Icon, label }) => (
          <NavLink
            key={to}
            to={to}
            style={({ isActive }) => ({
              display: 'flex',
              alignItems: 'center',
              gap: 12,
              padding: '11px 14px',
              borderRadius: 14,
              marginBottom: 6,
              textDecoration: 'none',
              color: isActive ? 'var(--text)' : 'var(--muted)',
              background: isActive ? 'linear-gradient(90deg, rgba(0, 112, 243, 0.28), rgba(73, 163, 255, 0.14))' : 'transparent',
              border: isActive ? '1px solid rgba(0, 112, 243, 0.42)' : '1px solid transparent',
              fontWeight: isActive ? 700 : 500,
              boxShadow: isActive ? 'inset 0 0 0 1px rgba(255,255,255,0.02)' : 'none',
            })}
          >
            <Icon size={16} />
            {label}
            {to === '/alerts' && liveAlertCount > 0 ? (
              <span style={{ marginLeft: 'auto', minWidth: 22, padding: '2px 7px', borderRadius: 999, background: 'rgba(255,71,87,0.22)', color: '#ff8c99', fontSize: 11, fontWeight: 800, textAlign: 'center' }}>
                {liveAlertCount > 99 ? '99+' : liveAlertCount}
              </span>
            ) : null}
          </NavLink>
        ))}
      </nav>

      <div style={{ padding: 14, borderTop: '1px solid rgba(0, 112, 243, 0.16)' }}>
        <button
          onClick={logout}
          className="btn-secondary"
          style={{
            width: '100%',
            padding: '11px 14px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            gap: 10,
          }}
        >
          <LogOut size={15} />
          Sign Out
        </button>
      </div>
    </aside>
  )
}
