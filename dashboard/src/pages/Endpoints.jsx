import { useEffect, useMemo, useState } from 'react'
import { Copy, Laptop, Monitor, Plus, Sparkles, X } from 'lucide-react'
import { agentAPI, dashboardAPI, responseAPI } from '../api/client'
import Topbar from '../components/Topbar'

const statusColor = { online: '#51d0a1', offline: '#86a6c7', isolated: '#ff6b6b' }

export default function Endpoints() {
  const [endpoints, setEndpoints] = useState([])
  const [selected, setSelected] = useState(null)
  const [events, setEvents] = useState([])
  const [showModal, setShowModal] = useState(false)
  const [newEp, setNewEp] = useState({ hostname: '', os: 'Windows', ip_address: '', mac_address: '' })
  const [agentResult, setAgentResult] = useState(null)
  const [msg, setMsg] = useState(null)
  const [filter, setFilter] = useState('all')
  const resolvedBackendUrl = useMemo(() => {
    const envBase = import.meta.env.VITE_API_BASE_URL
    if (envBase && envBase !== '/') return envBase.replace(/\/$/, '')
    return window.location.origin.replace(/\/$/, '')
  }, [])

  const fetch = () => dashboardAPI.endpoints().then(r => {
    setEndpoints(r.data)
    if (selected) {
      const nextSelected = r.data.find(item => item.id === selected.id)
      if (nextSelected) setSelected(nextSelected)
    }
  }).catch(console.error)

  useEffect(() => { fetch() }, [])

  const selectEp = ep => {
    setSelected(ep)
    dashboardAPI.endpointEvents(ep.id).then(r => setEvents(r.data)).catch(console.error)
  }

  const registerEp = async () => {
    try {
      const response = await agentAPI.register(newEp)
      setAgentResult(response.data)
      setMsg(null)
      fetch()
    } catch (error) {
      setMsg({ type: 'error', text: error.response?.data?.detail || 'Endpoint registration failed' })
    }
  }

  const isolate = async ep => {
    if (!window.confirm(`Isolate ${ep.hostname}? This immediately cuts network access.`)) return
    await responseAPI.isolate(ep.id, 'Manual isolation')
    fetch()
  }

  const restore = async ep => {
    await responseAPI.unisolate(ep.id)
    fetch()
  }

  const filteredEndpoints = useMemo(() => {
    if (filter === 'all') return endpoints
    return endpoints.filter(endpoint => endpoint.status === filter)
  }, [endpoints, filter])

  const copyText = async value => {
    try {
      await navigator.clipboard.writeText(value)
      setMsg({ type: 'success', text: 'Copied to clipboard' })
    } catch {
      setMsg({ type: 'error', text: 'Clipboard copy failed' })
    }
  }

  const rolloutConfig = agentResult ? `{\n  "backend_url": "${resolvedBackendUrl}",\n  "activation_code": "${agentResult.activation_code}",\n  "agent_token": "${agentResult.agent_token}",\n  "endpoint_id": "${agentResult.endpoint_id}",\n  "heartbeat_interval": 30,\n  "event_batch_interval": 10,\n  "version": "1.0.0"\n}` : null

  return (
    <div>
      <Topbar title="Endpoint Fleet" subtitle={`${endpoints.length} employee devices connected to Etherius`} onRefresh={fetch} />
      <div className="page-wrap">
        <div className="grid-two" style={{ marginBottom: 18 }}>
          <div className="panel" style={{ padding: 20 }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', gap: 14, alignItems: 'center', marginBottom: 16, flexWrap: 'wrap' }}>
              <div>
                <div className="display-heading" style={{ fontSize: 28, lineHeight: 1 }}>Device Operations</div>
                <div style={{ color: 'var(--muted)', marginTop: 6, fontSize: 13 }}>Managers can register, isolate, restore, and inspect employee machines from one control surface.</div>
              </div>
              <button className="btn-primary" onClick={() => { setShowModal(true); setAgentResult(null); setMsg(null) }} style={{ padding: '12px 18px', display: 'flex', alignItems: 'center', gap: 8 }}>
                <Plus size={15} />
                Register Endpoint
              </button>
            </div>

            <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap', marginBottom: 16 }}>
              {['all', 'online', 'offline', 'isolated'].map(value => (
                <button
                  key={value}
                  className="btn-secondary"
                  onClick={() => setFilter(value)}
                  style={{
                    padding: '8px 12px',
                    background: filter === value ? 'rgba(92, 200, 255, 0.14)' : undefined,
                    borderColor: filter === value ? 'rgba(92, 200, 255, 0.24)' : undefined,
                    textTransform: 'capitalize',
                  }}
                >
                  {value}
                </button>
              ))}
            </div>

            {filteredEndpoints.length === 0 ? (
              <div className="soft-note" style={{ textAlign: 'center', padding: '52px 24px' }}>
                <Monitor size={34} style={{ display: 'block', margin: '0 auto 12px', opacity: 0.5 }} />
                No endpoints match the current filter.
              </div>
            ) : (
              filteredEndpoints.map(ep => {
                const stateColor = statusColor[ep.status] || '#86a6c7'
                const risk = Number(ep.risk_score || 0)
                const riskColor = risk >= 70 ? '#ff6b6b' : risk >= 40 ? '#ffb347' : '#51d0a1'
                return (
                  <div
                    key={ep.id}
                    onClick={() => selectEp(ep)}
                    className="panel"
                    style={{
                      padding: 16,
                      marginBottom: 12,
                      cursor: 'pointer',
                      borderColor: selected?.id === ep.id ? 'rgba(92, 200, 255, 0.3)' : undefined,
                      background: selected?.id === ep.id ? 'linear-gradient(180deg, rgba(18, 34, 58, 0.98), rgba(8, 16, 30, 0.98))' : undefined,
                    }}
                  >
                    <div style={{ display: 'flex', justifyContent: 'space-between', gap: 12, alignItems: 'center', flexWrap: 'wrap' }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: 14 }}>
                        <div style={{
                          width: 48,
                          height: 48,
                          borderRadius: 16,
                          background: `${stateColor}18`,
                          border: `1px solid ${stateColor}22`,
                          display: 'grid',
                          placeItems: 'center',
                        }}>
                          <Laptop size={20} color={stateColor} />
                        </div>
                        <div>
                          <div style={{ fontWeight: 800, fontSize: 15 }}>{ep.hostname}</div>
                          <div style={{ color: 'var(--muted)', fontSize: 12, marginTop: 4 }}>{ep.os} · {ep.ip_address || 'No IP recorded'}</div>
                        </div>
                      </div>
                      <div style={{ display: 'flex', alignItems: 'center', gap: 12, flexWrap: 'wrap' }}>
                        <div style={{ textAlign: 'right' }}>
                          <div style={{ fontSize: 22, fontWeight: 900, color: riskColor, fontFamily: '"JetBrains Mono", monospace' }}>{risk}</div>
                          <div style={{ fontSize: 10, color: 'var(--muted)', textTransform: 'uppercase', letterSpacing: '0.12em' }}>Risk</div>
                        </div>
                        <span style={{ padding: '6px 12px', borderRadius: 999, background: `${stateColor}18`, color: stateColor, fontSize: 11, textTransform: 'uppercase', fontWeight: 800 }}>
                          {ep.status}
                        </span>
                        {ep.status !== 'isolated' ? (
                          <button className="btn-secondary" onClick={event => { event.stopPropagation(); isolate(ep) }} style={{ padding: '8px 12px', color: '#ff9a9a', borderColor: 'rgba(255, 107, 107, 0.18)' }}>
                            Isolate
                          </button>
                        ) : (
                          <button className="btn-secondary" onClick={event => { event.stopPropagation(); restore(ep) }} style={{ padding: '8px 12px', color: '#7ee0b9' }}>
                            Restore
                          </button>
                        )}
                      </div>
                    </div>
                  </div>
                )
              })
            )}
          </div>

          <div className="panel" style={{ padding: 20, position: 'sticky', top: 88, height: 'fit-content' }}>
            <div className="display-heading" style={{ fontSize: 26, lineHeight: 1, marginBottom: 14 }}>Employee Device Software</div>
            <div className="soft-note" style={{ marginBottom: 16 }}>
              The employee-side software is the <span className="kbd-box">agent</span> folder in this project. Each employee device runs that lightweight agent and sends telemetry back to the dashboard.
            </div>
            <div style={{ display: 'grid', gap: 10, marginBottom: 18 }}>
              <div className="soft-note"><strong>1.</strong> Register a device here.</div>
              <div className="soft-note"><strong>2.</strong> Copy the generated endpoint ID and agent token.</div>
              <div className="soft-note"><strong>3.</strong> Paste them into <span className="kbd-box">agent/agent_config.json</span> on the employee machine.</div>
              <div className="soft-note"><strong>4.</strong> Run <span className="kbd-box">EMPLOYEE_START_SHIELD.bat</span> on that machine.</div>
            </div>

            {selected ? (
              <>
                <div className="display-heading" style={{ fontSize: 24, lineHeight: 1, marginBottom: 12 }}>{selected.hostname}</div>
                <div className="soft-note" style={{ marginBottom: 16 }}>
                  <div><strong>Status:</strong> {selected.status}</div>
                  <div><strong>IP:</strong> {selected.ip_address || 'Not provided'}</div>
                  <div><strong>OS:</strong> {selected.os}</div>
                  <div><strong>Risk:</strong> {selected.risk_score}/100</div>
                </div>
                <div style={{ color: 'var(--muted)', fontSize: 12, textTransform: 'uppercase', letterSpacing: '0.12em', marginBottom: 10 }}>Recent Events</div>
                {events.length === 0 ? (
                  <div className="soft-note">No telemetry has been received for this device yet.</div>
                ) : events.map(event => (
                  <div key={event.id} className="soft-note" style={{ marginBottom: 10 }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', gap: 10 }}>
                      <strong style={{ textTransform: 'capitalize' }}>{event.event_type.replaceAll('_', ' ')}</strong>
                      <span style={{ color: Number(event.risk_score) > 60 ? '#ff9a9a' : 'var(--muted)' }}>{event.risk_score}/100</span>
                    </div>
                    <div style={{ marginTop: 6, color: 'var(--muted)' }}>{new Date(event.created_at).toLocaleString()}</div>
                  </div>
                ))}
              </>
            ) : (
              <div className="soft-note">Select an endpoint to inspect live device activity and response context.</div>
            )}
          </div>
        </div>

        {showModal ? (
          <div style={{ position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.78)', display: 'grid', placeItems: 'center', zIndex: 1000, padding: 20 }}>
            <div className="panel" style={{ width: 'min(760px, 100%)', padding: 26 }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 18 }}>
                <div>
                  <div className="display-heading" style={{ fontSize: 30, lineHeight: 1 }}>Register an employee device</div>
                  <div style={{ color: 'var(--muted)', marginTop: 6 }}>Create a secure link between the agent software and this dashboard.</div>
                </div>
                <button onClick={() => setShowModal(false)} style={{ background: 'transparent', border: 'none', color: 'var(--muted)', cursor: 'pointer' }}><X size={20} /></button>
              </div>

              {msg ? (
                <div className="soft-note" style={{ marginBottom: 16, borderColor: msg.type === 'success' ? 'rgba(81, 208, 161, 0.22)' : 'rgba(255, 107, 107, 0.22)', color: msg.type === 'success' ? '#7ee0b9' : '#ff9a9a' }}>
                  {msg.text}
                </div>
              ) : null}

              {!agentResult ? (
                <>
                  <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 14, marginBottom: 18 }}>
                    {[
                      ['Hostname', 'hostname', 'DESKTOP-ACCT-01'],
                      ['IP Address', 'ip_address', '10.0.4.23'],
                      ['MAC Address', 'mac_address', 'AA:BB:CC:DD:EE:FF'],
                    ].map(([label, key, placeholder]) => (
                      <div key={key}>
                        <label className="field-label">{label}</label>
                        <input className="field-input" value={newEp[key]} onChange={event => setNewEp({ ...newEp, [key]: event.target.value })} placeholder={placeholder} />
                      </div>
                    ))}
                    <div>
                      <label className="field-label">Operating System</label>
                      <select className="field-input" value={newEp.os} onChange={event => setNewEp({ ...newEp, os: event.target.value })}>
                        {['Windows', 'Linux', 'macOS'].map(option => <option key={option}>{option}</option>)}
                      </select>
                    </div>
                  </div>
                  <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 10 }}>
                    <button className="btn-secondary" onClick={() => setShowModal(false)} style={{ padding: '10px 14px' }}>Cancel</button>
                    <button className="btn-primary" onClick={registerEp} style={{ padding: '10px 14px' }}>Register Endpoint</button>
                  </div>
                </>
              ) : (
                <div className="grid-two">
                  <div className="soft-note">
                    <div style={{ display: 'flex', alignItems: 'center', gap: 10, color: '#7ee0b9', fontWeight: 800, marginBottom: 10 }}>
                      <Sparkles size={16} />
                      Device registered successfully
                    </div>
                    <div style={{ marginBottom: 12 }}><strong>Endpoint ID</strong><br />{agentResult.endpoint_id}</div>
                    <div style={{ marginBottom: 12 }}><strong>Activation Code</strong><br />{agentResult.activation_code}</div>
                    <div><strong>Agent Token</strong><br />{agentResult.agent_token}</div>
                  </div>
                  <div className="soft-note">
                    <div style={{ fontWeight: 800, marginBottom: 10 }}>agent_config.json</div>
                    <pre style={{ margin: 0, whiteSpace: 'pre-wrap', wordBreak: 'break-word', fontSize: 12, fontFamily: '"JetBrains Mono", monospace' }}>{rolloutConfig}</pre>
                    <div style={{ display: 'flex', gap: 10, marginTop: 14 }}>
                      <button className="btn-secondary" onClick={() => copyText(agentResult.activation_code)} style={{ padding: '8px 12px', display: 'flex', alignItems: 'center', gap: 8 }}><Copy size={14} /> Copy Activation Code</button>
                      <button className="btn-secondary" onClick={() => copyText(agentResult.agent_token)} style={{ padding: '8px 12px', display: 'flex', alignItems: 'center', gap: 8 }}><Copy size={14} /> Copy Token</button>
                      <button className="btn-secondary" onClick={() => copyText(rolloutConfig)} style={{ padding: '8px 12px', display: 'flex', alignItems: 'center', gap: 8 }}><Copy size={14} /> Copy Config</button>
                    </div>
                  </div>
                </div>
              )}
            </div>
          </div>
        ) : null}
      </div>
    </div>
  )
}
