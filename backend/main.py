"""
main.py
--------
FastAPI backend for the AI-Based Intelligent UAV Navigation System.

Endpoints:
  GET  /api/weather              -> current weather at a lat/lon
  GET  /api/risk                 -> risk score for a lat/lon (uses live weather)
  POST /api/route                -> A* route between two points, optional danger zones
  POST /api/simulate-storm       -> triggers a forced danger zone + reroute (demo button)
  WS   /ws/telemetry             -> live telemetry stream for the active route

Run locally:
  uvicorn main:app --reload --port 8000
"""

import asyncio
import os
from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from astar import find_path, DangerZone
from grid import BENGALURU, MYSURU
from risk import assess_risk, WeatherSnapshot
from telemetry import TelemetryState
from weather import fetch_weather, WeatherAPIError

load_dotenv()

# Shared in-memory state for the demo. A multi-user production system
# would key this per mission/session instead of using one global state.
telemetry_state = TelemetryState()
active_danger_zones: list[DangerZone] = []


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Seed an initial direct route on startup so the dashboard has
    # something to show immediately.
    result = find_path(*BENGALURU, *MYSURU, danger_zones=[])
    telemetry_state.set_route(result["waypoints"])
    yield


app = FastAPI(title="UAV Navigation & Risk Platform", lifespan=lifespan)

origins = os.getenv("CORS_ORIGINS", "http://localhost:5173").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class RouteRequest(BaseModel):
    start_lat: float = BENGALURU[0]
    start_lon: float = BENGALURU[1]
    end_lat: float = MYSURU[0]
    end_lon: float = MYSURU[1]


class StormRequest(BaseModel):
    lat: float
    lon: float
    radius_km: float = 25.0


@app.get("/api/health")
async def health():
    return {"status": "ok"}


@app.get("/api/weather")
async def get_weather(lat: float, lon: float):
    try:
        snapshot = await fetch_weather(lat, lon)
    except WeatherAPIError as e:
        raise HTTPException(status_code=502, detail=str(e))
    return snapshot.__dict__


@app.get("/api/risk")
async def get_risk(lat: float, lon: float):
    try:
        snapshot = await fetch_weather(lat, lon)
    except WeatherAPIError as e:
        raise HTTPException(status_code=502, detail=str(e))

    result = assess_risk(snapshot)
    return {
        "score": result.score,
        "level": result.level,
        "breakdown": result.breakdown,
        "weather": snapshot.__dict__,
    }


@app.post("/api/route")
async def post_route(req: RouteRequest):
    result = find_path(
        req.start_lat, req.start_lon, req.end_lat, req.end_lon,
        danger_zones=active_danger_zones,
    )
    telemetry_state.set_route(result["waypoints"])
    return result


@app.post("/api/simulate-storm")
async def simulate_storm(req: StormRequest):
    """
    Demo trigger: places a danger zone at the given point, forces a
    high-risk weather reading there, and recalculates the route with
    A* so it avoids the zone if a reasonable alternative exists.
    """
    global active_danger_zones
    active_danger_zones = [
        DangerZone(lat=req.lat, lon=req.lon, radius_km=req.radius_km, penalty_per_km=8.0)
    ]

    forced_weather = WeatherSnapshot(
        wind_speed_kmh=0, visibility_km=0, temperature_c=25,
        rain_probability_pct=0, condition="Clear",
    )
    risk_result = assess_risk(forced_weather, storm_override=True)

    route_result = find_path(
        *BENGALURU, *MYSURU, danger_zones=active_danger_zones,
    )
    telemetry_state.set_route(route_result["waypoints"])

    return {
        "danger_zone": {"lat": req.lat, "lon": req.lon, "radius_km": req.radius_km},
        "risk": {
            "score": risk_result.score,
            "level": risk_result.level,
            "breakdown": risk_result.breakdown,
        },
        "route": route_result,
    }


@app.post("/api/clear-storm")
async def clear_storm():
    global active_danger_zones
    active_danger_zones = []
    result = find_path(*BENGALURU, *MYSURU, danger_zones=[])
    telemetry_state.set_route(result["waypoints"])
    return result


@app.websocket("/ws/telemetry")
async def websocket_telemetry(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            snapshot = telemetry_state.tick()
            await websocket.send_json(snapshot)
            await asyncio.sleep(1.0)
    except WebSocketDisconnect:
        pass
