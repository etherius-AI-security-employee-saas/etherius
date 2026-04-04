import { useEffect, useState } from 'react'
import { Ban, Trash2 } from 'lucide-react'
import { dashboardAPI, responseAPI } from '../api/client'
import Topbar from '../components/Topbar'

export default function BlockedIPs() {
  const [ips, setIps] = useState([])

  const fetch = () => dashboardAPI.blockedIPs().then(r => setIps(r.data)).catch(console.error)
  useEffect(() => { fetch() }, [])

  const unblock = async id => {
    await responseAPI.unblockIP(id)
    fetch()
  }

  return (
    <div>
      <Topbar title="Blocked Network Sources" subtitle={`${ips.length} active containment rules`} onRefresh={fetch} />
      <div className="page-wrap">
        <div className="panel data-table">
          <div className="data-table-header" style={{ gridTemplateColumns: '1fr 2fr 1fr 110px' }}>
            <div>IP Address</div>
            <div>Reason</div>
            <div>Blocked At</div>
            <div>Action</div>
          </div>
          {ips.length === 0 ? (
            <div style={{ padding: '64px 40px', textAlign: 'center' }}>
              <Ban size={34} style={{ display: 'block', margin: '0 auto 12px', opacity: 0.45 }} />
              <div style={{ color: 'var(--muted)' }}>No IP addresses are currently blocked.</div>
            </div>
          ) : ips.map(ip => (
            <div key={ip.id} className="data-table-row" style={{ gridTemplateColumns: '1fr 2fr 1fr 110px' }}>
              <div style={{ fontFamily: '"JetBrains Mono", monospace', color: '#ff9a9a' }}>{ip.ip}</div>
              <div style={{ color: 'var(--muted-strong)' }}>{ip.reason || '-'}</div>
              <div style={{ color: 'var(--muted)' }}>{new Date(ip.created_at).toLocaleString()}</div>
              <button className="btn-secondary" onClick={() => unblock(ip.id)} style={{ padding: '8px 10px', display: 'flex', alignItems: 'center', gap: 6, color: '#ff9a9a' }}>
                <Trash2 size={13} />
                Unblock
              </button>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
