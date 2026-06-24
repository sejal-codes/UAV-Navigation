import { useEffect, useRef, useState } from 'react'

const WS_URL = import.meta.env.VITE_WS_URL || 'ws://localhost:8000/ws/telemetry'

export function useTelemetry() {
  const [telemetry, setTelemetry] = useState(null)
  const [connected, setConnected] = useState(false)
  const wsRef = useRef(null)

  useEffect(() => {
    let retryTimeout

    function connect() {
      const ws = new WebSocket(WS_URL)
      wsRef.current = ws

      ws.onopen = () => setConnected(true)
      ws.onclose = () => {
        setConnected(false)
        // Auto-reconnect for demo resilience (e.g. backend restart mid-demo)
        retryTimeout = setTimeout(connect, 2000)
      }
      ws.onerror = () => ws.close()
      ws.onmessage = (event) => {
        try {
          setTelemetry(JSON.parse(event.data))
        } catch {
          // ignore malformed frame
        }
      }
    }

    connect()

    return () => {
      clearTimeout(retryTimeout)
      wsRef.current?.close()
    }
  }, [])

  return { telemetry, connected }
}
