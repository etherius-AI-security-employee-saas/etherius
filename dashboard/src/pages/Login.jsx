import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Eye, EyeOff, KeyRound, Shield, Sparkles } from 'lucide-react'
import { authAPI } from '../api/client'
import BrandMark from '../components/BrandMark'
import { useAuth } from '../context/AuthContext'

const initialForm = {
  email: '',
  password: '',
  company_name: '',
  admin_full_name: '',
  domain: '',
  subscription_key: '',
}

export default function Login() {
  const [tab, setTab] = useState('login')
  const [showPass, setShowPass] = useState(false)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [form, setForm] = useState(initialForm)
  const { login } = useAuth()
  const navigate = useNavigate()
  const demoEmail = import.meta.env.VITE_DEMO_ADMIN_EMAIL || 'admin@etheriusdemo.com'
  const demoPassword = import.meta.env.VITE_DEMO_ADMIN_PASSWORD || 'Admin123!'
  const demoSubscriptionKey = import.meta.env.VITE_DEMO_SUBSCRIPTION_KEY || 'ETH-SUB-DEMO-2026-START'

  const set = key => e => setForm(prev => ({ ...prev, [key]: e.target.value }))

  const handleLogin = async e => {
    e.preventDefault()
    setError('')
    setLoading(true)
    try {
      await login(form.email, form.password)
      navigate('/dashboard')
    } catch (err) {
      setError(err.response?.data?.detail || 'Login failed')
    } finally {
      setLoading(false)
    }
  }

  const handleRegister = async e => {
    e.preventDefault()
    setError('')
    setLoading(true)
    try {
      await authAPI.register({
        company_name: form.company_name,
        domain: form.domain || null,
        admin_email: form.email,
        admin_password: form.password,
        admin_full_name: form.admin_full_name,
        subscription_key: form.subscription_key,
      })
      await login(form.email, form.password)
      navigate('/dashboard')
    } catch (err) {
      setError(err.response?.data?.detail || 'Registration failed')
    } finally {
      setLoading(false)
    }
  }

  const useDemoAdmin = () => {
    setError('')
    setTab('login')
    setForm(prev => ({
      ...prev,
      email: demoEmail,
      password: demoPassword,
    }))
  }

  return (
    <div style={{
      minHeight: '100vh',
      display: 'grid',
      placeItems: 'center',
      padding: 22,
      background:
        'radial-gradient(circle at top left, rgba(92, 200, 255, 0.2), transparent 28%), radial-gradient(circle at bottom right, rgba(0, 224, 184, 0.12), transparent 24%), linear-gradient(180deg, #07101c 0%, #02060d 100%)',
    }}>
      <div style={{
        width: 'min(1080px, 100%)',
        display: 'grid',
        gridTemplateColumns: '1.05fr 0.95fr',
        gap: 18,
      }}>
        <section className="panel" style={{
          padding: 36,
          minHeight: 640,
          display: 'flex',
          flexDirection: 'column',
          justifyContent: 'space-between',
          background:
            'radial-gradient(circle at top, rgba(92, 200, 255, 0.18), transparent 28%), linear-gradient(180deg, rgba(10, 23, 39, 0.98), rgba(5, 12, 21, 0.98))',
        }}>
          <div>
            <div style={{ marginBottom: 24 }}>
              <BrandMark />
            </div>
            <h1 style={{ margin: '16px 0 14px', fontSize: 56, lineHeight: 0.96, letterSpacing: '-0.06em' }}>
              Security operations that feel sharp, calm, and in control.
            </h1>
            <p style={{ color: 'var(--muted-strong)', fontSize: 16, lineHeight: 1.7, maxWidth: 520 }}>
              Monitor endpoints, manage alerts, and coordinate response actions from one clean command surface built for speed.
            </p>
          </div>

          <div style={{ display: 'grid', gap: 14 }}>
            {[
              'Fast company registration with a working local backend.',
              'Live endpoint, alert, and response workflows connected to the API.',
              'A cleaner visual system with fewer fragile setup assumptions.',
            ].map(item => (
              <div key={item} style={{
                display: 'flex',
                alignItems: 'center',
                gap: 12,
                padding: '14px 16px',
                borderRadius: 14,
                background: 'rgba(255,255,255,0.03)',
                border: '1px solid rgba(100, 181, 246, 0.12)',
              }}>
                <Sparkles size={16} color="var(--accent-2)" />
                <span style={{ color: 'var(--muted-strong)', fontSize: 14 }}>{item}</span>
              </div>
            ))}
          </div>
        </section>

        <section className="panel" style={{ padding: 30, alignSelf: 'stretch' }}>
          <div style={{ display: 'flex', gap: 8, padding: 6, borderRadius: 16, background: 'rgba(255,255,255,0.03)', marginBottom: 24 }}>
            {[
              ['login', 'Sign In'],
              ['register', 'Register Company'],
            ].map(([value, label]) => (
              <button
                key={value}
                type="button"
                onClick={() => { setTab(value); setError('') }}
                style={{
                  flex: 1,
                  padding: '12px 14px',
                  borderRadius: 12,
                  border: 'none',
                  cursor: 'pointer',
                  background: tab === value ? 'linear-gradient(135deg, rgba(31, 143, 255, 0.28), rgba(0, 201, 184, 0.16))' : 'transparent',
                  color: tab === value ? 'var(--text)' : 'var(--muted)',
                  fontWeight: tab === value ? 700 : 600,
                }}
              >
                {label}
              </button>
            ))}
          </div>

          <div style={{ marginBottom: 22 }}>
            <div style={{ fontSize: 28, fontWeight: 800, letterSpacing: '-0.05em' }}>
              {tab === 'login' ? 'Welcome back' : 'Create your workspace'}
            </div>
            <div style={{ color: 'var(--muted)', marginTop: 8 }}>
              {tab === 'login'
                ? 'Sign in to open the Etherius dashboard.'
                : 'Register a company and the admin account in one step.'}
            </div>
          </div>

          <div style={{
            marginBottom: 18,
            padding: '14px 16px',
            borderRadius: 14,
            background: 'rgba(92, 200, 255, 0.06)',
            border: '1px solid rgba(92, 200, 255, 0.14)',
          }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', gap: 12, alignItems: 'center', flexWrap: 'wrap' }}>
              <div>
                <div style={{ color: 'var(--accent)', fontSize: 11, fontWeight: 800, letterSpacing: '0.12em', textTransform: 'uppercase', marginBottom: 6 }}>
                  Demo Admin Ready
                </div>
                <div style={{ fontSize: 13, color: 'var(--muted-strong)', lineHeight: 1.6 }}>
                  Email: <strong>{demoEmail}</strong><br />
                  Password: <strong>{demoPassword}</strong><br />
                  Subscription Key: <strong>{demoSubscriptionKey}</strong>
                </div>
              </div>
              <button
                type="button"
                onClick={useDemoAdmin}
                className="btn-secondary"
                style={{ padding: '10px 14px', display: 'flex', alignItems: 'center', gap: 8 }}
              >
                <KeyRound size={14} />
                Use Demo Admin
              </button>
            </div>
          </div>

          {error ? (
            <div style={{
              marginBottom: 18,
              padding: '12px 14px',
              borderRadius: 12,
              border: '1px solid rgba(255, 107, 107, 0.25)',
              background: 'rgba(255, 107, 107, 0.08)',
              color: '#ff9a9a',
              fontSize: 14,
            }}>
              {error}
            </div>
          ) : null}

          <form onSubmit={tab === 'login' ? handleLogin : handleRegister}>
            {tab === 'register' ? (
              <>
                <div style={{ marginBottom: 16 }}>
                  <label className="field-label">Company Name</label>
                  <input className="field-input" value={form.company_name} onChange={set('company_name')} placeholder="Acme Security Labs" required />
                </div>
                <div style={{ marginBottom: 16 }}>
                  <label className="field-label">Admin Full Name</label>
                  <input className="field-input" value={form.admin_full_name} onChange={set('admin_full_name')} placeholder="Jane Carter" required />
                </div>
                <div style={{ marginBottom: 16 }}>
                  <label className="field-label">Company Domain</label>
                  <input className="field-input" value={form.domain} onChange={set('domain')} placeholder="acme.local" />
                </div>
                <div style={{ marginBottom: 16 }}>
                  <label className="field-label">Subscription Key</label>
                  <input className="field-input" value={form.subscription_key} onChange={set('subscription_key')} placeholder="ETH-SUB-XXXXX-XXXXX-XXXXX" required />
                </div>
              </>
            ) : null}

            <div style={{ marginBottom: 16 }}>
              <label className="field-label">Email Address</label>
              <input className="field-input" type="email" value={form.email} onChange={set('email')} placeholder="admin@company.com" required />
            </div>

            <div style={{ marginBottom: 22 }}>
              <label className="field-label">Password</label>
              <div style={{ position: 'relative' }}>
                <input
                  className="field-input"
                  type={showPass ? 'text' : 'password'}
                  value={form.password}
                  onChange={set('password')}
                  placeholder="Enter your password"
                  style={{ paddingRight: 44 }}
                  required
                />
                <button
                  type="button"
                  onClick={() => setShowPass(prev => !prev)}
                  style={{
                    position: 'absolute',
                    right: 12,
                    top: '50%',
                    transform: 'translateY(-50%)',
                    border: 'none',
                    background: 'transparent',
                    cursor: 'pointer',
                    color: 'var(--muted)',
                    display: 'grid',
                    placeItems: 'center',
                  }}
                >
                  {showPass ? <EyeOff size={16} /> : <Eye size={16} />}
                </button>
              </div>
            </div>

            <button
              type="submit"
              className="btn-primary"
              disabled={loading}
              style={{
                width: '100%',
                padding: '14px 16px',
                fontWeight: 800,
                fontSize: 15,
                opacity: loading ? 0.7 : 1,
                cursor: loading ? 'not-allowed' : 'pointer',
              }}
            >
              {loading ? 'Working...' : tab === 'login' ? 'Open Dashboard' : 'Create Company and Sign In'}
            </button>
          </form>

          <div style={{
            marginTop: 20,
            padding: '14px 16px',
            borderRadius: 14,
            background: 'rgba(255,255,255,0.03)',
            border: '1px solid rgba(100, 181, 246, 0.08)',
            color: 'var(--muted)',
            fontSize: 13,
            lineHeight: 1.6,
          }}>
            The backend now creates a local SQLite database automatically, seeds a demo admin in development, and populates example telemetry so the dashboard is useful immediately.
          </div>
        </section>
      </div>
    </div>
  )
}
