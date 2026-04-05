import { useState } from 'react'
import { AlertTriangle, ChevronDown, ChevronUp, Clock, Cpu, Monitor } from 'lucide-react'

const SEVERITY = { critical: '#ff6b6b', high: '#ff9f43', medium: '#ffd166', low: '#5cc8ff', info: '#7c93b1' }
const STATUS = { open: '#ff6b6b', investigating: '#ffd166', resolved: '#51d0a1', false_positive: '#7c93b1' }

export default function AlertCard({ alert, onUpdate }) {
  const [expanded, setExpanded] = useState(false)
  const severityColor = SEVERITY[alert.severity] || '#7c93b1'
  const statusColor = STATUS[alert.status] || '#7c93b1'
  const text = `${alert.title || ''} ${alert.description || ''}`.toLowerCase()
  const isDlp = text.includes('dlp') || text.includes('data loss') || text.includes('mass copy')

  return (
    <div className="panel" style={{
      padding: '18px 18px 16px',
      marginBottom: 12,
      borderLeft: `4px solid ${severityColor}`,
      borderTopLeftRadius: 14,
      borderBottomLeftRadius: 14,
    }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', gap: 16, alignItems: 'flex-start' }}>
        <div style={{ flex: 1 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 10, flexWrap: 'wrap' }}>
            <AlertTriangle size={14} color={severityColor} />
            <span style={{ fontSize: 15, fontWeight: 700 }}>{alert.title}</span>
            <span style={{ fontSize: 10, padding: '4px 10px', borderRadius: 999, background: `${severityColor}20`, color: severityColor, textTransform: 'uppercase', fontWeight: 800 }}>
              {alert.severity}
            </span>
            <span style={{ fontSize: 10, padding: '4px 10px', borderRadius: 999, background: `${statusColor}18`, color: statusColor, textTransform: 'uppercase', fontWeight: 700 }}>
              {alert.status}
            </span>
            {isDlp ? (
              <span style={{ fontSize: 10, padding: '4px 10px', borderRadius: 999, background: 'rgba(255,165,2,0.2)', color: '#ffa502', textTransform: 'uppercase', fontWeight: 800 }}>
                DLP
              </span>
            ) : null}
            <span style={{ marginLeft: 'auto', color: 'var(--accent)', fontSize: 12, fontWeight: 700 }}>
              Risk {alert.risk_score}/100
            </span>
          </div>

          <p style={{ margin: '0 0 10px', color: 'var(--muted-strong)', fontSize: 13, lineHeight: 1.65 }}>
            {alert.description}
          </p>

          <div style={{ display: 'flex', gap: 14, flexWrap: 'wrap', color: 'var(--muted)', fontSize: 12 }}>
            <span style={{ display: 'inline-flex', alignItems: 'center', gap: 6 }}>
              <Clock size={12} />
              {new Date(alert.created_at).toLocaleString()}
            </span>
            {alert.endpoint_id ? (
              <span style={{ display: 'inline-flex', alignItems: 'center', gap: 6 }}>
                <Monitor size={12} />
                Endpoint {alert.endpoint_id.slice(0, 8)}...
              </span>
            ) : null}
          </div>
        </div>

        <div style={{ display: 'flex', flexDirection: 'column', gap: 8, minWidth: 124 }}>
          {alert.status === 'open' && onUpdate ? (
            <button
              onClick={() => onUpdate(alert.id, { status: 'investigating' })}
              className="btn-secondary"
              style={{ padding: '8px 12px', color: '#ffd166', borderColor: 'rgba(255, 209, 102, 0.24)' }}
            >
              Investigate
            </button>
          ) : null}
          {alert.status === 'investigating' && onUpdate ? (
            <button
              onClick={() => onUpdate(alert.id, { status: 'resolved' })}
              className="btn-secondary"
              style={{ padding: '8px 12px', color: '#51d0a1', borderColor: 'rgba(81, 208, 161, 0.22)' }}
            >
              Resolve
            </button>
          ) : null}
          {alert.ai_explanation ? (
            <button
              onClick={() => setExpanded(prev => !prev)}
              className="btn-secondary"
              style={{ padding: '8px 12px', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 6 }}
            >
              <Cpu size={12} />
              AI
              {expanded ? <ChevronUp size={12} /> : <ChevronDown size={12} />}
            </button>
          ) : null}
        </div>
      </div>

      {expanded && alert.ai_explanation ? (
        <div style={{
          marginTop: 14,
          padding: '14px 16px',
          borderRadius: 14,
          background: 'rgba(92, 200, 255, 0.06)',
          border: '1px solid rgba(92, 200, 255, 0.14)',
        }}>
          <div style={{ color: 'var(--accent)', fontSize: 11, fontWeight: 800, marginBottom: 8, letterSpacing: '0.12em', textTransform: 'uppercase' }}>
            AI Security Analysis
          </div>
          <pre style={{
            margin: 0,
            whiteSpace: 'pre-wrap',
            color: 'var(--muted-strong)',
            fontSize: 12,
            lineHeight: 1.7,
            fontFamily: '"Segoe UI", Inter, sans-serif',
          }}>
            {alert.ai_explanation}
          </pre>
        </div>
      ) : null}
    </div>
  )
}
