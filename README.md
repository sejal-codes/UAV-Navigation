A mission-control style platform that monitors live weather conditions along a UAV flight corridor, computes a real-time risk score, and uses the **A* pathfinding algorithm** to recommend a safer alternate route when hazardous conditions (e.g. storms) are detected.

Built as a demonstration corridor between **Bengaluru and Mysuru, India**.

![status](https://img.shields.io/badge/status-prototype-orange) ![python](https://img.shields.io/badge/backend-FastAPI-009688) ![react](https://img.shields.io/badge/frontend-React-61dafb)

---

## What this actually is (read before the demo)

This is an **honest prototype**, not a claim of a production UAV system. Specifically:

- **Telemetry is simulated.** There is no physical drone. The telemetry module (`backend/telemetry.py`) generates a position along the active route at a realistic cruise speed, in a way that's architecturally ready to be replaced by a real GPS/IMU feed later.
- **Weather is real.** The system calls the live [OpenWeatherMap](https://openweathermap.org/api) API for current conditions.
- **Risk scoring is a transparent, rule-based weighted model** (wind, visibility, condition, rain probability), not a trained machine-learning classifier. This is intentional — it's explainable and auditable, which matters for any safety-relevant system. See `backend/risk.py` for the exact thresholds and weights.
- **Routing is real A\*** over a real lat/lon grid, with danger zones implemented as cost penalties (not hard walls) — see `backend/astar.py`.
- **No performance numbers are claimed** (e.g. "% reduction in flight time") because none were measured through real flight testing.

---

## Architecture
┌─────────────────────┐         WebSocket (live)        ┌──────────────────────┐

│   React Dashboard    │ ◄─────────────────────────────► │   FastAPI Backend     │

│   (Leaflet map,      │         REST (route/risk)        │   - A* router          │

│    risk gauge,       │ ◄─────────────────────────────► │   - Risk model         │

│    telemetry panel)  │                                   │   - Weather client    │

└─────────────────────┘                                   │   - Telemetry sim     │

└──────────┬────────────┘

│

▼

OpenWeatherMap API

## Project structure
uav-nav-system/

├── backend/

│   ├── main.py          # FastAPI app: REST endpoints + WebSocket telemetry stream

│   ├── grid.py           # Builds the navigable lat/lon grid for the BLR-MYS corridor

│   ├── astar.py           # A* pathfinding with danger-zone cost penalties

│   ├── risk.py             # Weighted risk-scoring model

│   ├── weather.py           # OpenWeatherMap API client

│   ├── telemetry.py          # Simulated UAV position along the active route

│   ├── requirements.txt

│   └── .env.example

└── frontend/

├── src/

│   ├── App.jsx            # Main dashboard layout

│   ├── MissionMap.jsx       # Leaflet map: route, danger zone, live UAV marker

│   ├── RiskGauge.jsx         # Radar-style risk score gauge

│   ├── StatTile.jsx           # Telemetry/weather stat tile

│   ├── api.js                  # REST client

│   └── useTelemetry.js          # WebSocket hook

├── package.json

└── .env.example

## Running locally

### 1. Backend

\`\`\`bash
cd backend
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt

cp .env.example .env
# edit .env and add your free API key from https://openweathermap.org/api

uvicorn main:app --reload --port 8000
\`\`\`

### 2. Frontend

\`\`\`bash
cd frontend
npm install
cp .env.example .env
npm run dev
\`\`\`

Open the printed local URL (default `http://localhost:5173`).

---

## How the core algorithm works

1. The Bengaluru → Mysuru corridor is converted into a 12×8 grid of real lat/lon waypoints (`grid.py`).
2. A* searches this grid using `f(n) = g(n) + h(n)`, where `g` is the real great-circle distance traveled so far and `h` is the straight-line (haversine) distance to the destination.
3. When "Simulate Storm" is triggered, a circular danger zone is placed at the corridor's midpoint. Any grid edge whose midpoint falls inside that zone gets a cost **penalty**, not a hard block — so A* prefers to route around it, but degrades gracefully rather than failing if no clear alternative exists.
4. The recalculated path, new distance, and whether it crosses the danger zone are returned to the frontend and rendered on the Leaflet map in real time.

## Honest impact framing

This is a prototype that was **not flight-tested**, so no performance percentages (flight time reduction, fuel savings, crash reduction, etc.) are claimed anywhere in this project. If asked about impact:

- Helps identify risky flight conditions earlier through continuous weather monitoring.
- Reduces reliance on manual replanning by automatically calculating alternate routes.
- Improves situational awareness through a centralized, real-time dashboard.
- Architecture is hardware-ready for future integration with real GPS/telemetry sources (e.g. ESP32-based modules).

## Future work

- Replace simulated telemetry with a real GPS/IMU feed.
- Multi-UAV support with per-mission session state.
- Forecast-based (not just current-conditions) risk scoring.
- Cloud deployment (AWS/Azure/GCP) for multi-operator access.

## License

MIT — see `LICENSE`.
