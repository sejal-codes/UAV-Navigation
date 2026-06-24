import { useEffect, useState, useCallback } from 'react'
import MissionMap from './MissionMap.jsx'
import RiskGauge from './RiskGauge.jsx'
import StatTile from './StatTile.jsx'
import { useTelemetry } from './useTelemetry.js'
import { api } from './api.js'

const BENGALURU = { lat: 12.9716, lon: 77.5946 }
const MYSURU = { lat: 12.2958, lon: 76.6394 }

export default function App() {
  const { telemetry, connected } = useTelemetry()

  const [waypoints, setWaypoints] = useState([])
  const [riskData, setRiskData] = useState(null)
  const [dangerZone, setDangerZone] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [stormActive, setStormActive] = useState(false)
  const [alerts, setAlerts] = useState([])

  const pushAlert = useCallback((message, tone = 'info') => {
    setAlerts((prev) => [{ id: Date.now(), message, tone }, ...prev].slice(0, 6))
  }, [])

  const loadRoute = useCallback(async () => {
    try {
      const result = await api.postRoute({
        start_lat: BENGALURU.lat,
        start_lon: BENGALURU.lon,
        end_lat: MYSURU.lat,
        end_lon: MYSURU.lon,
      })
      setWaypoints(result.waypoints)
    } catch (e) {
      setError(e.message)
    }
  }, [])

  const loadRisk = useCallback(async () => {
    try {
      setError(null)
      const data = await api.getRisk(BENGALURU.lat, BENGALURU.lon)
      setRiskData(data)
    } catch (e) {
      setError(e.message)
    }
  }, [])

  useEffect(() => {
    loadRoute()
    loadRisk()
    const interval = setInterval(loadRisk, 30000) // refresh live weather every 30s
    return () => clearInterval(interval)
  }, [loadRoute, loadRisk])

  async function handleSimulateStorm() {
    setLoading(true)
    setError(null)
    try {
      const midLat = (BENGALURU.lat + MYSURU.lat) / 2
      const midLon = (BENGALURU.lon + MYSURU.lon) / 2
      const result = await api.simulateStorm({ lat: midLat, lon: midLon, radius_km: 25 })
      setDangerZone(result.danger_zone)
      setWaypoints(result.route.waypoints)
      setRiskData({ score: result.risk.score, level: result.risk.level, breakdown: result.risk.breakdown, weather: riskData?.weather })
      setStormActive(true)
      pushAlert(`Danger zone detected on route — risk escalated to ${result.risk.level} (${result.risk.score}%)`, 'danger')
      pushAlert(`A* rerouted around hazard. New path: ${result.route.distance_km} km`, 'info')
    } catch (e) {
      setError(e.message)
    } finally {
      setLoading(false)
    }
  }

  async function handleClearStorm() {
    setLoading(true)
    setError(null)
    try {
      const result = await api.clearStorm()
      setWaypoints(result.waypoints)
      setDangerZone(null)
      setStormActive(false)
      pushAlert('Danger zone cleared. Route restored to direct path.', 'info')
      loadRisk()
    } catch (e) {
      setError(e.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div style={{ minHeight: '100vh', display: 'flex', flexDirection: 'column' }}>
      {/* Header */}
      <header
        style={{
          padding: '14px 24px',
          borderBottom: '1px solid var(--line)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
          <div
            style={{
              width: 10,
              height: 10,
              borderRadius: '50%',
              background: connected ? 'var(--accent-safe)' : 'var(--accent-danger)',
              boxShadow: connected ? '0 0 8px 2px rgba(61,220,132,0.6)' : 'none',
            }}
          />
          <h1 className="mono" style={{ fontSize: 16, margin: 0, letterSpacing: 1 }}>
            UAV MISSION CONTROL
          </h1>
          <span className="mono" style={{ fontSize: 11, color: 'var(--text-dim)' }}>
            BLR &rarr; MYS CORRIDOR
          </span>
        </div>
        <button
          onClick={stormActive ? handleClearStorm : handleSimulateStorm}
          disabled={loading}
          className="mono"
          style={{
            padding: '8px 18px',
            borderRadius: 6,
            border: `1px solid ${stormActive ? 'var(--accent-safe)' : 'var(--accent-danger)'}`,
            background: stormActive ? 'rgba(61,220,132,0.1)' : 'rgba(255,77,77,0.12)',
            color: stormActive ? 'var(--accent-safe)' : 'var(--accent-danger)',
            fontSize: 12,
            fontWeight: 700,
            letterSpacing: 1,
            cursor: loading ? 'wait' : 'pointer',
          }}
        >
          {loading ? 'PROCESSING...' : stormActive ? 'CLEAR STORM' : '⚡ SIMULATE STORM'}
        </button>
      </header>

      {error && (
        <div
          className="mono"
          style={{ padding: '8px 24px', background: 'rgba(255,77,77,0.1)', color: 'var(--accent-danger)', fontSize: 12 }}
        >
          ERROR: {error}
        </div>
      )}

      {/* Main grid */}
      <div style={{ flex: 1, display: 'grid', gridTemplateColumns: '280px 1fr 300px', gap: 16, padding: 16, minHeight: 0 }}>
        {/* Left panel: weather + risk */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
          <Panel title="Weather Intelligence">
            {riskData?.weather ? (
              <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                <StatTile label="Wind" value={riskData.weather.wind_speed_kmh} unit="km/h" />
                <StatTile label="Visibility" value={riskData.weather.visibility_km} unit="km" />
                <StatTile label="Condition" value={riskData.weather.condition} />
                <StatTile label="Temp" value={riskData.weather.temperature_c} unit="°C" />
              </div>
            ) : (
              <Placeholder text="Fetching live weather…" />
            )}
          </Panel>

          <Panel title="Risk Assessment">
            {riskData ? (
              <RiskGauge score={riskData.score} level={riskData.level} />
            ) : (
              <Placeholder text="Calculating risk…" />
            )}
          </Panel>
        </div>

        {/* Center: map */}
        <div style={{ minHeight: 0, borderRadius: 8, overflow: 'hidden', border: '1px solid var(--line)' }}>
          <MissionMap waypoints={waypoints} dangerZone={dangerZone} telemetry={telemetry} />
        </div>

        {/* Right panel: telemetry + alerts */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
          <Panel title="Live Telemetry">
            {telemetry ? (
              <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                <StatTile label="Speed" value={telemetry.speed_kmh} unit="km/h" accent="var(--accent-info)" />
                <StatTile label="Altitude" value={telemetry.altitude_m} unit="m" />
                <StatTile label="Heading" value={telemetry.heading_deg} unit="°" />
                <StatTile label="Progress" value={telemetry.progress_pct} unit="%" />
                <div className="mono" style={{ fontSize: 10, color: 'var(--text-dim)', marginTop: 4 }}>
                  SOURCE: {telemetry.source?.toUpperCase()}
                </div>
              </div>
            ) : (
              <Placeholder text="Connecting telemetry…" />
            )}
          </Panel>

          <Panel title="Mission Alerts" grow>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 8, overflowY: 'auto' }}>
              {alerts.length === 0 && <Placeholder text="No alerts. Nominal flight." />}
              {alerts.map((a) => (
                <div
                  key={a.id}
                  className="mono"
                  style={{
                    fontSize: 11,
                    padding: '8px 10px',
                    borderRadius: 6,
                    background: a.tone === 'danger' ? 'rgba(255,77,77,0.1)' : 'rgba(61,169,252,0.08)',
                    borderLeft: `3px solid ${a.tone === 'danger' ? 'var(--accent-danger)' : 'var(--accent-info)'}`,
                    color: 'var(--text-primary)',
                  }}
                >
                  {a.message}
                </div>
              ))}
            </div>
          </Panel>
        </div>
      </div>
    </div>
  )
}

function Panel({ title, children, grow }) {
  return (
    <div
      style={{
        background: 'var(--bg-panel)',
        border: '1px solid var(--line)',
        borderRadius: 10,
        padding: 14,
        display: 'flex',
        flexDirection: 'column',
        flex: grow ? 1 : 'none',
        minHeight: 0,
      }}
    >
      <div className="mono" style={{ fontSize: 11, color: 'var(--text-dim)', letterSpacing: 1, marginBottom: 10 }}>
        {title.toUpperCase()}
      </div>
      <div style={{ flex: 1, minHeight: 0 }}>{children}</div>
    </div>
  )
}

function Placeholder({ text }) {
  return <div className="mono" style={{ fontSize: 12, color: 'var(--text-dim)' }}>{text}</div>
}
