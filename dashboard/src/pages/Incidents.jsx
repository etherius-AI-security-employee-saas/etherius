import { useState } from 'react'
import { AlertTriangle, Sparkles } from 'lucide-react'
import { responseAPI } from '../api/client'
import Topbar from '../components/Topbar'

export default function Incidents() {
  const [ip, setIp] = useState('')
  const [reason, setReason] = useState('')
  const [msg, setMsg] = useState(null)
  const [loading, setLoading] = useState(false)

  const blockIP = async () => {
    if (!ip) return
    setLoading(true)
    setMsg(null)
    try {
      await responseAPI.blockIP(ip, reason || 'Manual block')
      setMsg({ type: 'success', text: `IP ${ip} blocked successfully` })
      setIp('')
      setReason('')
    } catch (error) {
      setMsg({ type: 'error', text: error.response?.data?.detail || 'Failed to block IP address' })
    } finally {
      setLoading(false)
    }
  }

  return (
    <div>
      <Topbar title="Response Center" subtitle="Contain threats quickly and guide managers through the right actions" />
      <div className="page-wrap">
        <div className="grid-two">
          <div>
            <div className="panel" style={{ padding: 22, marginBottom: 18 }}>
              <div className="display-heading" style={{ fontSize: 30, lineHeight: 1 }}>Immediate containment</div>
              <div style={{ color: 'var(--muted)', marginTop: 8, marginBottom: 18, fontSize: 14 }}>
                Use this area to block malicious IP addresses while the rest of the team investigates the affected employee device.
              </div>

              {msg ? (
                <div className="soft-note" style={{ marginBottom: 18, borderColor: msg.type === 'success' ? 'rgba(81, 208, 161, 0.24)' : 'rgba(255, 107, 107, 0.24)', color: msg.type === 'success' ? '#7ee0b9' : '#ff9a9a' }}>
                  {msg.text}
                </div>
              ) : null}

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 14, marginBottom: 16 }}>
                <div>
                  <label className="field-label">Malicious IP Address</label>
                  <input className="field-input" value={ip} onChange={event => setIp(event.target.value)} placeholder="185.77.21.19" />
                </div>
                <div>
                  <label className="field-label">Reason</label>
                  <input className="field-input" value={reason} onChange={event => setReason(event.target.value)} placeholder="Credential attack from external source" />
                </div>
              </div>

              <button className="btn-primary" disabled={loading || !ip} onClick={blockIP} style={{ padding: '12px 18px', opacity: loading || !ip ? 0.7 : 1 }}>
                {loading ? 'Blocking...' : 'Block IP Now'}
              </button>
            </div>

            <div className="panel" style={{ padding: 22 }}>
              <div className="display-heading" style={{ fontSize: 28, lineHeight: 1, marginBottom: 14 }}>Manager playbook</div>
              {[
                ['1', 'Open Alerts and confirm which user or endpoint is affected.'],
                ['2', 'Use the Endpoint Fleet page to isolate the machine if spread is possible.'],
                ['3', 'Block the attacking IP here when external containment is needed.'],
                ['4', 'Review the Audit Trail so every response action is documented.'],
              ].map(([step, text]) => (
                <div key={step} className="soft-note" style={{ marginBottom: 10, display: 'flex', gap: 14, alignItems: 'flex-start' }}>
                  <span className="kbd-box">{step}</span>
                  <span>{text}</span>
                </div>
              ))}
            </div>
          </div>

          <div>
            <div className="panel" style={{ padding: 22, marginBottom: 18 }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 14 }}>
                <AlertTriangle size={18} color="#ffb347" />
                <strong>Automated response profile</strong>
              </div>
              {[
                ['Risk score 80+', 'Critical escalation and urgent manager review'],
                ['Risk score 60+', 'High-priority alert with analyst triage'],
                ['Risk score 40+', 'Medium alert and monitoring trail'],
                ['Brute-force login burst', 'Immediate alert and optional IP block'],
                ['Suspicious process execution', 'Critical flagging and containment recommendation'],
              ].map(([rule, action]) => (
                <div key={rule} className="soft-note" style={{ marginBottom: 10 }}>
                  <strong>{rule}</strong>
                  <div style={{ marginTop: 6, color: 'var(--muted)' }}>{action}</div>
                </div>
              ))}
            </div>

            <div className="panel" style={{ padding: 22 }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 14 }}>
                <Sparkles size={18} color="#5cc8ff" />
                <strong>How employees connect to the dashboard</strong>
              </div>
              <div className="soft-note" style={{ marginBottom: 10 }}>
                The employee-side software is the local agent. It watches process, network, login, and file activity on each machine.
              </div>
              <div className="soft-note" style={{ marginBottom: 10 }}>
                That telemetry is sent to the backend, scored for risk, and shown here as alerts for managers and admins.
              </div>
              <div className="soft-note">
                Keep tokens private. Only place endpoint tokens on their intended employee devices and rotate them if you suspect exposure.
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
