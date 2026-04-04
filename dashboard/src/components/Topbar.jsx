import { RefreshCw } from 'lucide-react'

export default function Topbar({ title, subtitle, onRefresh }) {
  return (
    <header style={{
      minHeight: 72,
      background: 'rgba(11, 10, 27, 0.72)',
      backdropFilter: 'blur(20px)',
      borderBottom: '1px solid rgba(153, 117, 255, 0.16)',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'space-between',
      gap: 16,
      padding: '16px 28px',
      position: 'sticky',
      top: 0,
      zIndex: 50,
    }}>
      <div>
        <h1 style={{ margin: 0, fontSize: 25, fontWeight: 800, letterSpacing: '-0.02em' }}>{title}</h1>
        {subtitle ? <div style={{ color: 'var(--muted)', marginTop: 6, fontSize: 13 }}>{subtitle}</div> : null}
      </div>

      <div style={{ display: 'flex', alignItems: 'center', gap: 12, flexWrap: 'wrap' }}>
        <div className="status-pill">
          <span style={{ width: 8, height: 8, borderRadius: '50%', background: 'currentColor', boxShadow: '0 0 10px currentColor' }} />
          Live telemetry
        </div>
        {onRefresh ? (
          <button
            onClick={onRefresh}
            className="btn-secondary"
            style={{ padding: '10px 14px', display: 'flex', alignItems: 'center', gap: 8 }}
          >
            <RefreshCw size={14} />
            Refresh
          </button>
        ) : null}
      </div>
    </header>
  )
}
