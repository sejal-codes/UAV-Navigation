export default function StatTile({ label, value, unit, accent }) {
  return (
    <div
      style={{
        background: 'var(--bg-panel-raised)',
        border: '1px solid var(--line)',
        borderRadius: 8,
        padding: '10px 14px',
        flex: 1,
        minWidth: 0,
      }}
    >
      <div className="mono" style={{ fontSize: 10, color: 'var(--text-dim)', letterSpacing: 1, marginBottom: 4 }}>
        {label.toUpperCase()}
      </div>
      <div className="mono" style={{ fontSize: 20, fontWeight: 700, color: accent || 'var(--text-primary)' }}>
        {value}
        {unit && <span style={{ fontSize: 12, color: 'var(--text-dim)', marginLeft: 4 }}>{unit}</span>}
      </div>
    </div>
  )
}
