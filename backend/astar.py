"""
astar.py
---------
Real A* pathfinding over the grid defined in grid.py.

Standard A*: f(n) = g(n) + h(n)
  g(n) = actual cost so far to reach node n
  h(n) = heuristic estimate of remaining cost (straight-line distance to goal)

Danger zones are implemented as a cost PENALTY added to g(n) for any
node that falls inside the zone's radius -- not as a hard "wall." This
means: if a danger zone fully blocks the corridor, A* will still find a
path through it if there is truly no alternative; but if a clear
alternative path exists, the penalty makes A* prefer it. This is the
actual mechanism behind "avoids the storm zone."
"""

import heapq
import math
from dataclasses import dataclass

from grid import Node, build_grid, neighbors, nearest_node

EARTH_RADIUS_KM = 6371.0


@dataclass
class DangerZone:
    lat: float
    lon: float
    radius_km: float
    penalty_per_km: float  # extra cost added per km traveled inside the zone


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Great-circle distance between two lat/lon points, in km."""
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = (
        math.sin(dphi / 2) ** 2
        + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    )
    return 2 * EARTH_RADIUS_KM * math.asin(math.sqrt(a))


def edge_cost(a: Node, b: Node, danger_zones: list[DangerZone]) -> float:
    """
    Cost of moving from node a to node b: real distance in km, plus a
    penalty if the midpoint of the edge falls inside any danger zone.
    """
    base = haversine_km(a.lat, a.lon, b.lat, b.lon)

    mid_lat = (a.lat + b.lat) / 2
    mid_lon = (a.lon + b.lon) / 2

    penalty = 0.0
    for zone in danger_zones:
        dist_to_zone_center = haversine_km(mid_lat, mid_lon, zone.lat, zone.lon)
        if dist_to_zone_center <= zone.radius_km:
            penalty += base * zone.penalty_per_km

    return base + penalty


def find_path(
    start_lat: float,
    start_lon: float,
    end_lat: float,
    end_lon: float,
    danger_zones: list[DangerZone] | None = None,
) -> dict:
    """
    Runs A* between the grid nodes nearest to the given start/end
    coordinates. Returns the path as a list of {lat, lon} waypoints
    plus total distance and whether any danger zone was crossed.
    """
    danger_zones = danger_zones or []
    nodes = build_grid()

    start = nearest_node(nodes, start_lat, start_lon)
    goal = nearest_node(nodes, end_lat, end_lon)

    def h(n: Node) -> float:
        return haversine_km(n.lat, n.lon, goal.lat, goal.lon)

    open_set: list[tuple[float, str]] = [(h(start), start.id)]
    came_from: dict[str, str] = {}
    g_score: dict[str, float] = {start.id: 0.0}
    f_score: dict[str, float] = {start.id: h(start)}
    visited: set[str] = set()

    while open_set:
        _, current_id = heapq.heappop(open_set)
        if current_id in visited:
            continue
        visited.add(current_id)
        current = nodes[current_id]

        if current_id == goal.id:
            # Reconstruct path
            path_ids = [current_id]
            while path_ids[-1] in came_from:
                path_ids.append(came_from[path_ids[-1]])
            path_ids.reverse()

            waypoints = [
                {"lat": nodes[nid].lat, "lon": nodes[nid].lon} for nid in path_ids
            ]
            total_km = g_score[goal.id]

            crossed_danger = any(
                any(
                    haversine_km(wp["lat"], wp["lon"], z.lat, z.lon) <= z.radius_km
                    for z in danger_zones
                )
                for wp in waypoints
            )

            return {
                "waypoints": waypoints,
                "distance_km": round(total_km, 2),
                "nodes_explored": len(visited),
                "crosses_danger_zone": crossed_danger,
            }

        for r, c in neighbors(current):
            neighbor = nodes[f"{r}-{c}"]
            if neighbor.id in visited:
                continue

            tentative_g = g_score[current_id] + edge_cost(current, neighbor, danger_zones)

            if tentative_g < g_score.get(neighbor.id, math.inf):
                came_from[neighbor.id] = current_id
                g_score[neighbor.id] = tentative_g
                f_score[neighbor.id] = tentative_g + h(neighbor)
                heapq.heappush(open_set, (f_score[neighbor.id], neighbor.id))

    # No path found at all (should not happen on a fully connected grid)
    return {
        "waypoints": [],
        "distance_km": 0.0,
        "nodes_explored": len(visited),
        "crosses_danger_zone": False,
    }
