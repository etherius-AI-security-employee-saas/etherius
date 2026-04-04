import { useEffect, useState } from 'react'
import { Activity } from 'lucide-react'
import { dashboardAPI } from '../api/client'
import Topbar from '../components/Topbar'

const actionColor = {
  LOGIN: '#51d0a1',
  CREATE_USER: '#5cc8ff',
  BLOCK_IP: '#ff6b6b',
  ISOLATE: '#ffb347',
  REGISTER_ENDPOINT: '#8fbcff',
  default: '#86a6c7',
}

export default function AuditLog() {
  const [logs, setLogs] = useState([])
  const fetch = () => dashboardAPI.auditLogs().then(r => setLogs(r.data)).catch(console.error)

  useEffect(() => { fetch() }, [])

  return (
    <div>
      <Topbar title="Audit Trail" subtitle="Manager actions and security operations history" onRefresh={fetch} />
      <div className="page-wrap">
        <div className="panel data-table">
          <div className="data-table-header" style={{ gridTemplateColumns: '170px 1fr 1fr 170px' }}>
            <div>Action</div>
            <div>Resource</div>
            <div>Details</div>
            <div>Time</div>
          </div>
          {logs.length === 0 ? (
            <div style={{ padding: '64px 40px', textAlign: 'center' }}>
              <Activity size={34} style={{ display: 'block', margin: '0 auto 12px', opacity: 0.45 }} />
              <div style={{ color: 'var(--muted)' }}>No audit entries exist yet.</div>
            </div>
          ) : logs.map(log => {
            const color = actionColor[log.action] || actionColor.default
            return (
              <div key={log.id} className="data-table-row" style={{ gridTemplateColumns: '170px 1fr 1fr 170px' }}>
                <div>
                  <span style={{ padding: '6px 12px', borderRadius: 999, background: `${color}18`, color, fontSize: 11, fontWeight: 800, textTransform: 'uppercase' }}>
                    {log.action}
                  </span>
                </div>
                <div style={{ fontFamily: '"JetBrains Mono", monospace', color: 'var(--muted-strong)', fontSize: 12 }}>{log.resource || '-'}</div>
                <div style={{ color: 'var(--muted)' }}>{log.details || '-'}</div>
                <div style={{ color: 'var(--muted)' }}>{new Date(log.created_at).toLocaleString()}</div>
              </div>
            )
          })}
        </div>
      </div>
    </div>
  )
}
