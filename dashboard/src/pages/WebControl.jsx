import { useEffect, useState } from 'react'
import Topbar from '../components/Topbar'
import { dashboardAPI } from '../api/client'


const PRESETS = {
  gambling: ['bet365.com', '1xbet.com', 'stake.com'],
  adult: ['xvideos.com', 'pornhub.com', 'xnxx.com'],
  social: ['facebook.com', 'instagram.com', 'tiktok.com'],
}


export default function WebControl() {
  const [domains, setDomains] = useState([])
  const [history, setHistory] = useState([])
  const [domain, setDomain] = useState('')
  const [category, setCategory] = useState('custom')

  const fetchAll = () => {
    Promise.all([
      dashboardAPI.blockedDomains(),
      dashboardAPI.events({ event_type: 'web', limit: 100 }),
    ])
      .then(([domainResponse, historyResponse]) => {
        setDomains(domainResponse.data || [])
        setHistory(historyResponse.data || [])
      })
      .catch(console.error)
  }

  useEffect(() => {
    fetchAll()
  }, [])

  const addDomain = async () => {
    if (!domain.trim()) return
    await dashboardAPI.addBlockedDomain({ domain: domain.trim(), category, is_active: true })
    setDomain('')
    setCategory('custom')
    fetchAll()
  }

  const removeDomain = async id => {
    await dashboardAPI.removeBlockedDomain(id)
    fetchAll()
  }

  const addPreset = async preset => {
    const list = PRESETS[preset] || []
    for (const item of list) {
      // eslint-disable-next-line no-await-in-loop
      await dashboardAPI.addBlockedDomain({ domain: item, category: preset, is_active: true })
    }
    fetchAll()
  }

  return (
    <div>
      <Topbar title="Web Control" subtitle="Block domains and monitor browsing policy violations" onRefresh={fetchAll} />
      <div className="page-wrap">
        <div className="panel" style={{ padding: 18, marginBottom: 16 }}>
          <div style={{ fontWeight: 800, marginBottom: 10 }}>Add Blocked Domain</div>
          <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
            <input className="field-input" placeholder="example.com" value={domain} onChange={event => setDomain(event.target.value)} style={{ minWidth: 240 }} />
            <select className="field-input" value={category} onChange={event => setCategory(event.target.value)} style={{ width: 170 }}>
              <option value="custom">Custom</option>
              <option value="gambling">Gambling</option>
              <option value="adult">Adult</option>
              <option value="social">Social Media</option>
            </select>
            <button className="btn-primary" onClick={addDomain} style={{ padding: '10px 16px' }}>Add Domain</button>
          </div>
          <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap', marginTop: 12 }}>
            {Object.keys(PRESETS).map(item => (
              <button key={item} className="btn-secondary" onClick={() => addPreset(item)} style={{ padding: '7px 10px', textTransform: 'capitalize' }}>
                Add {item} preset
              </button>
            ))}
          </div>
        </div>

        <div className="grid-two">
          <div className="panel" style={{ padding: 18 }}>
            <div style={{ fontWeight: 800, marginBottom: 10 }}>Blocked Domains</div>
            {domains.length === 0 ? (
              <div className="soft-note">No blocked domains configured yet.</div>
            ) : (
              <div style={{ display: 'grid', gap: 10 }}>
                {domains.map(item => (
                  <div key={item.id} className="soft-note">
                    <div style={{ display: 'flex', justifyContent: 'space-between', gap: 12 }}>
                      <div>
                        <div style={{ fontWeight: 700 }}>{item.domain}</div>
                        <div style={{ marginTop: 4, color: 'var(--muted)', fontSize: 12 }}>
                          {item.category || 'custom'} | {item.is_active ? 'Active' : 'Disabled'}
                        </div>
                      </div>
                      <button className="btn-secondary" onClick={() => removeDomain(item.id)} style={{ padding: '7px 10px', color: '#ff4757' }}>Disable</button>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>

          <div className="panel" style={{ padding: 18 }}>
            <div style={{ fontWeight: 800, marginBottom: 10 }}>Browsing Violations</div>
            {history.length === 0 ? (
              <div className="soft-note">No web policy violations recorded yet.</div>
            ) : (
              <div style={{ display: 'grid', gap: 8, maxHeight: 560, overflow: 'auto' }}>
                {history.map(item => (
                  <div key={item.id} className="soft-note">
                    <div style={{ fontWeight: 700 }}>{item.payload?.domain || 'Unknown domain'}</div>
                    <div style={{ marginTop: 4, color: 'var(--muted)', fontSize: 12 }}>{item.payload?.url || ''}</div>
                    <div style={{ marginTop: 4, color: '#ffa502', fontSize: 12 }}>{item.payload?.category || 'custom'}</div>
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
