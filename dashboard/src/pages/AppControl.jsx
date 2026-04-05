import { useEffect, useState } from 'react'
import Topbar from '../components/Topbar'
import { dashboardAPI } from '../api/client'


export default function AppControl() {
  const [entries, setEntries] = useState([])
  const [history, setHistory] = useState([])
  const [appName, setAppName] = useState('')
  const [action, setAction] = useState('kill')

  const fetchAll = () => {
    Promise.all([
      dashboardAPI.appBlacklist(),
      dashboardAPI.events({ event_type: 'app_blacklist', limit: 100 }),
    ])
      .then(([entryResponse, historyResponse]) => {
        setEntries(entryResponse.data || [])
        setHistory(historyResponse.data || [])
      })
      .catch(console.error)
  }

  useEffect(() => {
    fetchAll()
  }, [])

  const addEntry = async () => {
    if (!appName.trim()) return
    await dashboardAPI.addAppBlacklist({ app_name: appName.trim().toLowerCase(), action })
    setAppName('')
    setAction('kill')
    fetchAll()
  }

  const removeEntry = async id => {
    await dashboardAPI.removeAppBlacklist(id)
    fetchAll()
  }

  return (
    <div>
      <Topbar title="App Control" subtitle="Blacklist dangerous applications and enforce alert/kill actions" onRefresh={fetchAll} />
      <div className="page-wrap">
        <div className="panel" style={{ padding: 18, marginBottom: 16 }}>
          <div style={{ fontWeight: 800, marginBottom: 10 }}>Add Blacklisted Application</div>
          <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
            <input className="field-input" placeholder="e.g. mimikatz, netcat, tor" value={appName} onChange={event => setAppName(event.target.value)} style={{ minWidth: 260 }} />
            <select className="field-input" value={action} onChange={event => setAction(event.target.value)} style={{ width: 150 }}>
              <option value="kill">Auto-Kill</option>
              <option value="alert">Alert Only</option>
            </select>
            <button className="btn-primary" onClick={addEntry} style={{ padding: '10px 16px' }}>Add</button>
          </div>
        </div>

        <div className="grid-two">
          <div className="panel" style={{ padding: 18 }}>
            <div style={{ fontWeight: 800, marginBottom: 10 }}>Blacklist Entries</div>
            {entries.length === 0 ? (
              <div className="soft-note">No entries configured.</div>
            ) : (
              <div style={{ display: 'grid', gap: 10 }}>
                {entries.map(item => (
                  <div key={item.id} className="soft-note">
                    <div style={{ display: 'flex', justifyContent: 'space-between', gap: 10 }}>
                      <div>
                        <div style={{ fontWeight: 700 }}>{item.app_name}</div>
                        <div style={{ color: 'var(--muted)', marginTop: 4, fontSize: 12 }}>Action: {item.action === 'kill' ? 'Auto-Kill' : 'Alert Only'}</div>
                      </div>
                      <button className="btn-secondary" onClick={() => removeEntry(item.id)} style={{ color: '#ff4757', padding: '7px 10px' }}>Remove</button>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>

          <div className="panel" style={{ padding: 18 }}>
            <div style={{ fontWeight: 800, marginBottom: 10 }}>Blocked App Attempts</div>
            {history.length === 0 ? (
              <div className="soft-note">No blocked app attempts recorded yet.</div>
            ) : (
              <div style={{ display: 'grid', gap: 8, maxHeight: 560, overflow: 'auto' }}>
                {history.map(item => (
                  <div key={item.id} className="soft-note">
                    <div style={{ fontWeight: 700 }}>{item.payload?.process_name || 'Unknown process'}</div>
                    <div style={{ marginTop: 4, color: 'var(--muted)', fontSize: 12 }}>User: {item.payload?.username || 'unknown'}</div>
                    <div style={{ marginTop: 4, color: 'var(--muted)', fontSize: 12 }}>Action: {item.payload?.action || 'alert'} | Killed: {String(item.payload?.killed)}</div>
                    <div style={{ marginTop: 4, color: 'var(--muted)', fontSize: 12 }}>{new Date(item.created_at).toLocaleString()}</div>
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
