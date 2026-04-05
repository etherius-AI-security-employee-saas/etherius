import { useEffect, useMemo, useState } from 'react'
import Topbar from '../components/Topbar'
import { dashboardAPI } from '../api/client'


function scoreColor(score) {
  const value = Number(score || 0)
  if (value >= 60) return '#ff4757'
  if (value >= 30) return '#ffa502'
  return '#2ed573'
}


export default function InsiderThreats() {
  const [rows, setRows] = useState([])
  const [selectedId, setSelectedId] = useState('')
  const [loading, setLoading] = useState(true)

  const fetchScores = () => {
    dashboardAPI.insiderScores({ recalculate: true })
      .then(response => {
        const data = response.data || []
        setRows(data)
        if (!selectedId && data[0]?.endpoint_id) setSelectedId(data[0].endpoint_id)
      })
      .catch(console.error)
      .finally(() => setLoading(false))
  }

  useEffect(() => {
    fetchScores()
  }, [])

  const selected = useMemo(() => rows.find(item => item.endpoint_id === selectedId) || null, [rows, selectedId])

  return (
    <div>
      <Topbar title="Insider Threats" subtitle="AI risk scoring by employee behavior and policy violations" onRefresh={fetchScores} />
      <div className="page-wrap">
        <div className="grid-two">
          <div className="panel" style={{ padding: 18 }}>
            <div style={{ fontWeight: 800, marginBottom: 10 }}>Risk Leaderboard</div>
            {loading ? (
              <div className="soft-note">Calculating insider threat scores...</div>
            ) : rows.length === 0 ? (
              <div className="soft-note">No endpoints available for scoring yet.</div>
            ) : (
              <div style={{ display: 'grid', gap: 10 }}>
                {rows.map((item, index) => (
                  <button
                    key={item.endpoint_id}
                    onClick={() => setSelectedId(item.endpoint_id)}
                    className="soft-note"
                    style={{
                      textAlign: 'left',
                      cursor: 'pointer',
                      borderColor: selectedId === item.endpoint_id ? 'rgba(0,112,243,0.35)' : undefined,
                      background: selectedId === item.endpoint_id ? 'rgba(0,112,243,0.08)' : undefined,
                    }}
                  >
                    <div style={{ display: 'flex', justifyContent: 'space-between', gap: 10 }}>
                      <div>
                        <div style={{ color: 'var(--muted)', fontSize: 11 }}>#{index + 1}</div>
                        <div style={{ fontWeight: 800 }}>{item.hostname}</div>
                        <div style={{ marginTop: 4, color: 'var(--muted)', fontSize: 12 }}>Trend: {item.trend}</div>
                      </div>
                      <div style={{ fontSize: 26, fontWeight: 900, color: scoreColor(item.score) }}>{item.score}</div>
                    </div>
                  </button>
                ))}
              </div>
            )}
          </div>

          <div className="panel" style={{ padding: 18 }}>
            <div style={{ fontWeight: 800, marginBottom: 10 }}>Selected Employee Insight</div>
            {!selected ? (
              <div className="soft-note">Select an endpoint from the leaderboard.</div>
            ) : (
              <div>
                <div style={{ fontWeight: 900, fontSize: 18 }}>{selected.hostname}</div>
                <div style={{ color: scoreColor(selected.score), fontSize: 28, fontWeight: 900, marginTop: 4 }}>{selected.score}</div>
                <div style={{ marginTop: 4, color: 'var(--muted)', fontSize: 12 }}>Trend: {selected.trend} | Last updated {new Date(selected.calculated_at).toLocaleString()}</div>

                <div style={{ marginTop: 14 }}>
                  <div style={{ fontWeight: 700, marginBottom: 8 }}>Score Timeline</div>
                  <div style={{ display: 'flex', alignItems: 'flex-end', gap: 6, height: 100 }}>
                    {(selected.timeline || []).slice(-16).map((point, idx) => (
                      <div key={`${selected.endpoint_id}-${idx}`} style={{ flex: 1, minWidth: 8 }}>
                        <div style={{ height: `${Math.max(8, Number(point.score || 0))}%`, background: scoreColor(point.score), borderRadius: 6, opacity: 0.8 }} />
                      </div>
                    ))}
                  </div>
                </div>

                <div style={{ marginTop: 14 }}>
                  <div style={{ fontWeight: 700, marginBottom: 8 }}>Driving Factors</div>
                  <div style={{ display: 'grid', gap: 8 }}>
                    {(selected.factors || []).map((item, idx) => (
                      <div key={`${selected.endpoint_id}-factor-${idx}`} className="soft-note" style={{ margin: 0 }}>
                        {item}
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
