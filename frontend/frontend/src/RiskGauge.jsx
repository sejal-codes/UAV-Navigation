const LEVEL_COLOR = {
  Safe: 'var(--accent-safe)',
  Caution: 'var(--accent-caution)',
  Danger: 'var(--accent-danger)',
}

export default function RiskGauge({ score, level }) {
  const color = LEVEL_COLOR[level] || 'var(--text-dim)'
  const radius = 70
  const circumference = Math.PI * radius // half circle
  const offset = circumference - (score / 100) * circumference

  return (
    <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
      <svg width="180" height="100" viewBox="0 0 180 100">
        <path
          d="M 10 90 A 70 70 0 0 1 170 90"
          fill="none"
          stroke="var(--line)"
          strokeWidth="10"
          strokeLinecap="round"
        />
        <path
          d="M 10 90 A 70 70 0 0 1 170 90"
          fill="none"
          stroke={color}
          strokeWidth="10"
          strokeLinecap="round"
          strokeDasharray={circumference}
          strokeDashoffset={offset}
          style={{ transition: 'stroke-dashoffset 0.6s ease, stroke 0.6s ease' }}
        />
        <text x="90" y="75" textAnchor="middle" fontSize="28" fontFamily="JetBrains Mono" fill="var(--text-primary)" fontWeight="700">
          {score}
        </text>
        <text x="90" y="92" textAnchor="middle" fontSize="10" fontFamily="JetBrains Mono" fill="var(--text-dim)" letterSpacing="1">
          RISK SCORE
        </text>
      </svg>
      <div
        className="mono"
        style={{
          marginTop: 4,
          padding: '4px 14px',
          borderRadius: 999,
          fontSize: 12,
          fontWeight: 700,
          letterSpacing: 1,
          color,
          border: `1px solid ${color}`,
          background: `${color}1a`,
        }}
      >
        {level?.toUpperCase()}
      </div>
    </div>
  )
}
