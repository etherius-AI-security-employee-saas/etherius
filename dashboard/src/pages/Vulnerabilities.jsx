import { useEffect, useState } from 'react'
import Topbar from '../components/Topbar'
import { dashboardAPI } from '../api/client'


export default function Vulnerabilities() {
  const [data, setData] = useState({ endpoints: [], known_watchlist: [] })
  const [selected, setSelected] = useState('')

  const fetchData = () => {
    dashboardAPI.vulnerabilities()
      .then(response => {
        const next = response.data || { endpoints: [], known_watchlist: [] }
        setData(next)
        if (!selected && next.endpoints?.[0]?.endpoint_id) setSelected(next.endpoints[0].endpoint_id)
      })
      .catch(console.error)
  }

  useEffect(() => {
    fetchData()
  }, [])

  const selectedEndpoint = (data.endpoints || []).find(item => item.endpoint_id === selected) || null

  return (
    <div>
      <Topbar title="Vulnerabilities" subtitle="Software inventory scanning and CVE risk visibility" onRefresh={fetchData} />
      <div className="page-wrap">
        <div className="grid-two">
          <div className="panel" style={{ padding: 18 }}>
            <div style={{ fontWeight: 800, marginBottom: 10 }}>Per-Endpoint Vulnerability Counts</div>
            {(data.endpoints || []).length === 0 ? (
              <div className="soft-note">No vulnerability inventory received yet.</div>
            ) : (
              <div style={{ display: 'grid', gap: 10 }}>
                {(data.endpoints || []).map(item => (
                  <button
                    key={item.endpoint_id}
                    onClick={() => setSelected(item.endpoint_id)}
                    className="soft-note"
                    style={{
                      textAlign: 'left',
                      cursor: 'pointer',
                      borderColor: selected === item.endpoint_id ? 'rgba(0,112,243,0.35)' : undefined,
                      background: selected === item.endpoint_id ? 'rgba(0,112,243,0.08)' : undefined,
                    }}
                  >
                    <div style={{ display: 'flex', justifyContent: 'space-between', gap: 10 }}>
                      <div style={{ fontWeight: 700 }}>{item.endpoint_id}</div>
                      <div style={{ color: item.critical_count > 0 ? '#ff4757' : '#ffa502', fontWeight: 800 }}>
                        {item.vuln_count} vulnerabilities
                      </div>
                    </div>
                    <div style={{ marginTop: 4, color: 'var(--muted)', fontSize: 12 }}>Critical: {item.critical_count}</div>
                  </button>
                ))}
              </div>
            )}
          </div>

          <div className="panel" style={{ padding: 18 }}>
            <div style={{ fontWeight: 800, marginBottom: 10 }}>Vulnerability Details</div>
            {!selectedEndpoint ? (
              <div className="soft-note">Select an endpoint to view CVE details.</div>
            ) : (
              <div style={{ display: 'grid', gap: 8, maxHeight: 560, overflow: 'auto' }}>
                {selectedEndpoint.items.map(item => (
                  <div key={item.id} className="soft-note">
                    <div style={{ fontWeight: 700 }}>{item.software_name}</div>
                    <div style={{ marginTop: 4, color: 'var(--muted)', fontSize: 12 }}>Version: {item.version || 'unknown'}</div>
                    <div style={{ marginTop: 4, color: item.is_vulnerable ? '#ff4757' : '#2ed573', fontSize: 12, fontWeight: 700 }}>
                      {item.is_vulnerable ? `Needs Update (${item.severity || 'risk'})` : 'Up to date'}
                    </div>
                    {item.cve_id ? <div style={{ marginTop: 4, color: '#ffa502', fontSize: 12 }}>{item.cve_id}</div> : null}
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
