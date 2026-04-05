import { useEffect, useState } from 'react'
import { Activity, AlertTriangle, Ban, HardDrive, LogIn, LogOut, Monitor, Shield, Usb, Zap } from 'lucide-react'
import { Area, AreaChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import { dashboardAPI } from '../api/client'
import AlertCard from '../components/AlertCard'
import StatCard from '../components/StatCard'
import Topbar from '../components/Topbar'

const MOCK_CHART = [
  { t: '00:00', score: 5 }, { t: '04:00', score: 8 }, { t: '08:00', score: 42 },
  { t: '10:00', score: 30 }, { t: '12:00', score: 65 }, { t: '14:00', score: 38 },
  { t: '16:00', score: 78 }, { t: '18:00', score: 55 }, { t: '20:00', score: 30 }, { t: '24:00', score: 12 },
]

function ChartTooltip({ active, payload }) {
  if (!active || !payload?.length) return null
  return (
    <div className="panel" style={{ padding: '10px 12px', borderRadius: 12 }}>
      <div style={{ color: 'var(--accent)', fontWeight: 700, fontSize: 12 }}>Risk Score: {payload[0].value}</div>
    </div>
  )
}

export default function Dashboard() {
  const [stats, setStats] = useState(null)
  const [recentAlerts, setRecentAlerts] = useState([])
  const [loading, setLoading] = useState(true)

  const fetchAll = () => {
    Promise.all([
      dashboardAPI.stats(),
      dashboardAPI.alerts({ status: 'open', limit: 5 }),
    ])
      .then(([statsResponse, alertsResponse]) => {
        setStats(statsResponse.data)
        setRecentAlerts(alertsResponse.data)
      })
      .catch(console.error)
      .finally(() => setLoading(false))
  }

  useEffect(() => {
    fetchAll()
    const interval = setInterval(fetchAll, 30000)
    return () => clearInterval(interval)
  }, [])

  const handleUpdate = async (id, data) => {
    await dashboardAPI.updateAlert(id, data)
    fetchAll()
  }

  return (
    <div>
      <Topbar title="Security Overview" subtitle="Real-time threat monitoring and response posture" onRefresh={fetchAll} />
      <div className="page-wrap">
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(190px, 1fr))', gap: 16, marginBottom: 24 }}>
          <StatCard
            icon={Monitor}
            label="Total Endpoints"
            value={stats?.total_endpoints}
            color="#5cc8ff"
            sub={`${stats?.online_endpoints ?? 0} online - ${stats?.offline_endpoints ?? 0} offline`}
          />
          <StatCard icon={AlertTriangle} label="Open Alerts" value={stats?.open_alerts} color="#ffb347" />
          <StatCard icon={Zap} label="Critical" value={stats?.critical_alerts} color="#ff6b6b" sub="Needs immediate attention" />
          <StatCard icon={Activity} label="Events Today" value={stats?.events_today} color="#51d0a1" />
          <StatCard icon={LogIn} label="Logins Today" value={stats?.login_events_today} color="#5cc8ff" />
          <StatCard icon={LogOut} label="Logouts Today" value={stats?.logout_events_today} color="#ffba52" />
          <StatCard icon={Ban} label="Blocked IPs" value={stats?.blocked_ips} color="#ffd166" />
          <StatCard icon={Usb} label="USB Events" value={stats?.usb_events_today} color="#0070f3" />
          <StatCard icon={HardDrive} label="DLP Events" value={stats?.dlp_events_today} color="#ffa502" />
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: '2fr 1fr', gap: 16, marginBottom: 24 }}>
          <div className="panel" style={{ padding: 22 }}>
            <div style={{ fontSize: 14, fontWeight: 800, marginBottom: 16 }}>Risk Score Timeline</div>
            <ResponsiveContainer width="100%" height={220}>
              <AreaChart data={MOCK_CHART}>
                <defs>
                  <linearGradient id="riskGlow" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#5cc8ff" stopOpacity={0.45} />
                    <stop offset="95%" stopColor="#5cc8ff" stopOpacity={0.02} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(134, 166, 199, 0.12)" />
                <XAxis dataKey="t" tick={{ fill: '#86a6c7', fontSize: 11 }} axisLine={false} tickLine={false} />
                <YAxis domain={[0, 100]} tick={{ fill: '#86a6c7', fontSize: 11 }} axisLine={false} tickLine={false} />
                <Tooltip content={<ChartTooltip />} />
                <Area type="monotone" dataKey="score" stroke="#5cc8ff" strokeWidth={2.4} fill="url(#riskGlow)" />
              </AreaChart>
            </ResponsiveContainer>
          </div>

          <div className="panel" style={{ padding: 22 }}>
            <div style={{ fontSize: 14, fontWeight: 800, marginBottom: 16 }}>Alert Breakdown</div>
            {[
              { label: 'Critical', value: stats?.critical_alerts ?? 0, color: '#ff6b6b' },
              { label: 'High', value: stats?.high_alerts ?? 0, color: '#ff9f43' },
              { label: 'Open Total', value: stats?.open_alerts ?? 0, color: '#ffd166' },
            ].map(item => (
              <div key={item.label} style={{ marginBottom: 16 }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 6, fontSize: 12 }}>
                  <span style={{ color: 'var(--muted)' }}>{item.label}</span>
                  <strong style={{ color: item.color }}>{item.value}</strong>
                </div>
                <div style={{ height: 6, borderRadius: 999, background: 'rgba(255,255,255,0.06)' }}>
                  <div
                    style={{
                      height: '100%',
                      borderRadius: 999,
                      width: `${Math.min((item.value / Math.max(stats?.open_alerts || 1, 1)) * 100, 100)}%`,
                      background: item.color,
                      transition: 'width 0.35s',
                    }}
                  />
                </div>
              </div>
            ))}

            <div style={{
              marginTop: 24,
              padding: '12px 14px',
              borderRadius: 14,
              background: 'rgba(81, 208, 161, 0.08)',
              border: '1px solid rgba(81, 208, 161, 0.16)',
              display: 'flex',
              alignItems: 'center',
              gap: 10,
            }}>
              <Shield size={16} color="#51d0a1" />
              <div>
                <div style={{ color: '#51d0a1', fontWeight: 700, fontSize: 12 }}>AI Engine Active</div>
                <div style={{ color: 'var(--muted)', fontSize: 12 }}>Telemetry and risk scoring are online.</div>
              </div>
            </div>
          </div>
        </div>

        <div className="panel" style={{ padding: 22 }}>
          <div style={{ fontSize: 14, fontWeight: 800, marginBottom: 16 }}>Recent Open Alerts</div>
          {loading ? (
            <div style={{ color: 'var(--muted)', fontSize: 14 }}>Loading alerts...</div>
          ) : recentAlerts.length === 0 ? (
            <div style={{ textAlign: 'center', padding: '34px 0', color: 'var(--muted)' }}>
              <Shield size={34} style={{ margin: '0 auto 10px', display: 'block', opacity: 0.45 }} />
              <div>No open alerts. The system is currently clear.</div>
            </div>
          ) : (
            recentAlerts.map(alert => <AlertCard key={alert.id} alert={alert} onUpdate={handleUpdate} />)
          )}
        </div>
      </div>
    </div>
  )
}
