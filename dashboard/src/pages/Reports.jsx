import { useEffect, useState } from 'react'
import Topbar from '../components/Topbar'
import { dashboardAPI } from '../api/client'


export default function Reports() {
  const [days, setDays] = useState(30)
  const [summary, setSummary] = useState(null)
  const [loading, setLoading] = useState(true)

  const fetchSummary = () => {
    setLoading(true)
    dashboardAPI.reportSummary({ days })
      .then(response => setSummary(response.data))
      .catch(console.error)
      .finally(() => setLoading(false))
  }

  useEffect(() => {
    fetchSummary()
  }, [days])

  const downloadPdf = async () => {
    const response = await dashboardAPI.reportPdf({ days })
    const blob = new Blob([response.data], { type: 'application/pdf' })
    const href = URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = href
    link.download = `etherius-security-summary-${days}d.pdf`
    document.body.appendChild(link)
    link.click()
    link.remove()
    URL.revokeObjectURL(href)
  }

  return (
    <div>
      <Topbar title="Compliance Reports" subtitle="Executive and manager security posture reporting" onRefresh={fetchSummary} />
      <div className="page-wrap">
        <div className="panel" style={{ padding: 18, marginBottom: 16, display: 'flex', gap: 10, alignItems: 'center', flexWrap: 'wrap' }}>
          <label className="field-label" style={{ margin: 0 }}>Date Range (days)</label>
          <select className="field-input" value={days} onChange={event => setDays(Number(event.target.value))} style={{ width: 140 }}>
            {[7, 14, 30, 60, 90].map(item => <option key={item} value={item}>{item}</option>)}
          </select>
          <button className="btn-secondary" onClick={fetchSummary} style={{ padding: '10px 14px' }}>Refresh</button>
          <button className="btn-primary" onClick={downloadPdf} style={{ padding: '10px 14px' }}>Download PDF</button>
        </div>

        {loading || !summary ? (
          <div className="panel" style={{ padding: 20 }}>Loading report...</div>
        ) : (
          <div className="grid-two">
            <div className="panel" style={{ padding: 18 }}>
              <div style={{ fontWeight: 800, marginBottom: 10 }}>Compliance Score</div>
              <div style={{ fontSize: 44, fontWeight: 900, color: summary.compliance_score >= 70 ? '#2ed573' : summary.compliance_score >= 40 ? '#ffa502' : '#ff4757' }}>
                {summary.compliance_score}
              </div>
              <div style={{ color: 'var(--muted)', marginTop: 4, fontSize: 12 }}>0-100 weighted by alerts and policy violations</div>

              <div style={{ marginTop: 16, display: 'grid', gap: 8 }}>
                {[
                  ['Critical Alerts', summary.alerts_by_severity?.critical || 0],
                  ['High Alerts', summary.alerts_by_severity?.high || 0],
                  ['Policy Violations', summary.policy_violations || 0],
                  ['Blocked Threats', summary.blocked_threats_count || 0],
                ].map(item => (
                  <div key={item[0]} className="soft-note" style={{ margin: 0, display: 'flex', justifyContent: 'space-between' }}>
                    <span>{item[0]}</span>
                    <strong>{item[1]}</strong>
                  </div>
                ))}
              </div>
            </div>

            <div className="panel" style={{ padding: 18 }}>
              <div style={{ fontWeight: 800, marginBottom: 10 }}>Alerts Over Time</div>
              <div style={{ display: 'flex', alignItems: 'flex-end', gap: 6, height: 120, marginBottom: 14 }}>
                {(summary.alerts_over_time || []).slice(-20).map(item => (
                  <div key={item.date} style={{ flex: 1 }}>
                    <div style={{ height: `${Math.max(6, Math.min(100, item.count * 10))}%`, background: '#0070f3', borderRadius: 6, opacity: 0.75 }} />
                  </div>
                ))}
              </div>
              <div style={{ fontWeight: 800, marginBottom: 8 }}>Top Threats</div>
              <div style={{ display: 'grid', gap: 8 }}>
                {(summary.top_threats || []).map(item => (
                  <div key={item.event_type} className="soft-note" style={{ margin: 0, display: 'flex', justifyContent: 'space-between' }}>
                    <span style={{ textTransform: 'capitalize' }}>{String(item.event_type || '').replaceAll('_', ' ')}</span>
                    <strong>{item.count}</strong>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
