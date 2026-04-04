export default function StatCard({ icon: Icon, label, value, color, sub }) {
  return (
    <div
      className="panel"
      style={{
        padding: '22px 22px 20px',
        position: 'relative',
        overflow: 'hidden',
        transition: 'transform 0.2s, box-shadow 0.2s',
      }}
      onMouseOver={e => {
        e.currentTarget.style.transform = 'translateY(-3px)'
        e.currentTarget.style.boxShadow = `0 18px 36px ${color}22`
      }}
      onMouseOut={e => {
        e.currentTarget.style.transform = 'translateY(0)'
        e.currentTarget.style.boxShadow = ''
      }}
    >
      <div style={{
        position: 'absolute',
        inset: 0,
        background: `radial-gradient(circle at top right, ${color}20, transparent 35%)`,
        pointerEvents: 'none',
      }} />
      <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', gap: 16 }}>
        <div>
          <div style={{
            color: 'var(--muted)',
            fontSize: 11,
            textTransform: 'uppercase',
            letterSpacing: '0.12em',
            fontWeight: 700,
            marginBottom: 12,
          }}>
            {label}
          </div>
          <div style={{ fontSize: 36, fontWeight: 900, lineHeight: 1, letterSpacing: '-0.05em' }}>
            {value ?? '-'}
          </div>
          {sub ? <div style={{ color, marginTop: 8, fontSize: 12 }}>{sub}</div> : null}
        </div>
        <div style={{
          width: 46,
          height: 46,
          borderRadius: 16,
          background: `${color}18`,
          border: `1px solid ${color}22`,
          display: 'grid',
          placeItems: 'center',
        }}>
          <Icon size={20} color={color} />
        </div>
      </div>
    </div>
  )
}
