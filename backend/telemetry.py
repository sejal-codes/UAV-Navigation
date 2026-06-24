"""
telemetry.py
-------------
Simulates UAV telemetry (position, altitude, speed, heading) moving
along the currently active route.

This is explicitly SIMULATED, not from real hardware -- be upfront
about that in any demo or viva. The architecture, however, is written
so that swapping this for a real GPS/IMU feed (e.g. from an
ESP32 + GPS module reporting over MQTT or serial-to-WebSocket bridge)
would only require replacing this module; the dashboard, risk engine,
and routing logic don't change.
"""

import math
import time
from dataclasses import dataclass, field


@dataclass
class TelemetryState:
    waypoints: list[dict] = field(default_factory=list)
    progress: float = 0.0       # 0.0 -> 1.0 along the route
    speed_kmh: float = 45.0      # typical small-UAV cruise speed
    altitude_m: float = 120.0
    last_tick: float = field(default_factory=time.time)

    def set_route(self, waypoints: list[dict]):
        self.waypoints = waypoints
        self.progress = 0.0

    def tick(self) -> dict:
        """Advances simulated position along the route based on elapsed time."""
        now = time.time()
        dt = now - self.last_tick
        self.last_tick = now

        if len(self.waypoints) < 2:
            return self._snapshot(self.waypoints[0] if self.waypoints else {"lat": 0, "lon": 0}, 0)

        total_km = self._route_length_km()
        if total_km == 0:
            return self._snapshot(self.waypoints[0], 0)

        km_per_second = self.speed_kmh / 3600.0
        self.progress += (km_per_second * dt) / total_km
        if self.progress >= 1.0:
            self.progress = 0.0  # loop the demo route

        position, heading = self._interpolate(self.progress)
        return self._snapshot(position, heading)

    def _route_length_km(self) -> float:
        total = 0.0
        for a, b in zip(self.waypoints[:-1], self.waypoints[1:]):
            total += self._haversine(a["lat"], a["lon"], b["lat"], b["lon"])
        return total

    def _interpolate(self, progress: float) -> tuple[dict, float]:
        target_km = progress * self._route_length_km()
        accumulated = 0.0
        for a, b in zip(self.waypoints[:-1], self.waypoints[1:]):
            seg_km = self._haversine(a["lat"], a["lon"], b["lat"], b["lon"])
            if accumulated + seg_km >= target_km or seg_km == 0:
                local_t = 0.0 if seg_km == 0 else (target_km - accumulated) / seg_km
                lat = a["lat"] + (b["lat"] - a["lat"]) * local_t
                lon = a["lon"] + (b["lon"] - a["lon"]) * local_t
                heading = self._bearing(a["lat"], a["lon"], b["lat"], b["lon"])
                return {"lat": lat, "lon": lon}, heading
            accumulated += seg_km
        last = self.waypoints[-1]
        return {"lat": last["lat"], "lon": last["lon"]}, 0.0

    @staticmethod
    def _haversine(lat1, lon1, lat2, lon2) -> float:
        R = 6371.0
        phi1, phi2 = math.radians(lat1), math.radians(lat2)
        dphi = math.radians(lat2 - lat1)
        dlambda = math.radians(lon2 - lon1)
        a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
        return 2 * R * math.asin(math.sqrt(a))

    @staticmethod
    def _bearing(lat1, lon1, lat2, lon2) -> float:
        phi1, phi2 = math.radians(lat1), math.radians(lat2)
        dlambda = math.radians(lon2 - lon1)
        x = math.sin(dlambda) * math.cos(phi2)
        y = math.cos(phi1) * math.sin(phi2) - math.sin(phi1) * math.cos(phi2) * math.cos(dlambda)
        return (math.degrees(math.atan2(x, y)) + 360) % 360

    def _snapshot(self, position: dict, heading: float) -> dict:
        return {
            "lat": round(position.get("lat", 0), 6),
            "lon": round(position.get("lon", 0), 6),
            "altitude_m": self.altitude_m,
            "speed_kmh": self.speed_kmh,
            "heading_deg": round(heading, 1),
            "progress_pct": round(self.progress * 100, 1),
            "source": "simulated",
        }
