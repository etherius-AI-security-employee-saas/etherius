export default function BrandMark({ compact = false }) {
  const iconSize = compact ? 42 : 54
  return (
    <div className="brand-mark" style={compact ? { gap: 10 } : undefined}>
      <div
        className="brand-logo"
        style={{
          width: iconSize,
          height: iconSize,
          borderRadius: compact ? 14 : 18,
          display: 'grid',
          placeItems: 'center',
          background: 'linear-gradient(145deg, #0d1321, #101b30)',
          border: '1px solid rgba(0,112,243,0.34)',
          boxShadow: '0 14px 28px rgba(0, 112, 243, 0.22)',
        }}
      >
        <div style={{
          width: compact ? 16 : 22,
          height: compact ? 20 : 26,
          border: '2px solid #49a3ff',
          borderTop: '3px solid #0070f3',
          borderRadius: '7px 7px 11px 11px',
          transform: 'translateY(-1px)',
        }} />
      </div>
      <div>
        <div className="brand-title" style={compact ? { fontSize: 28 } : undefined}>ETHERIUS</div>
        <div className="brand-subtitle">Security Operations Platform</div>
      </div>
    </div>
  )
}
