const BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

async function handle(res) {
  if (!res.ok) {
    const body = await res.json().catch(() => ({}))
    throw new Error(body.detail || `Request failed: ${res.status}`)
  }
  return res.json()
}

export const api = {
  getWeather: (lat, lon) =>
    fetch(`${BASE_URL}/api/weather?lat=${lat}&lon=${lon}`).then(handle),

  getRisk: (lat, lon) =>
    fetch(`${BASE_URL}/api/risk?lat=${lat}&lon=${lon}`).then(handle),

  postRoute: (body) =>
    fetch(`${BASE_URL}/api/route`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    }).then(handle),

  simulateStorm: (body) =>
    fetch(`${BASE_URL}/api/simulate-storm`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    }).then(handle),

  clearStorm: () =>
    fetch(`${BASE_URL}/api/clear-storm`, { method: 'POST' }).then(handle),
}
