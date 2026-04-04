export default function BrandMark({ compact = false }) {
  return (
    <div className="brand-mark" style={compact ? { gap: 10 } : undefined}>
      <img
        src="/etherius-logo.jpeg"
        alt="Etherius logo"
        className="brand-logo"
        style={compact ? { width: 42, height: 42, borderRadius: 14 } : undefined}
      />
      <div>
        <div className="brand-title" style={compact ? { fontSize: 28 } : undefined}>etherius</div>
        <div className="brand-subtitle">Security Operations Platform</div>
      </div>
    </div>
  )
}
