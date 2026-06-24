"""
grid.py
--------
Converts the real-world Bengaluru -> Mysuru corridor into a grid of
waypoints that the A* algorithm can search over.

We don't need a literal road network for a UAV (it flies point-to-point,
not on roads), so we build a rectangular lat/lon grid that *bounds* the
corridor, with enough columns/rows to give A* meaningful alternate paths
when a danger zone blocks the direct line.

This keeps the algorithm honest: it is real grid-based A*, not a fake
animation. Coordinates are real GPS coordinates the whole way through.
"""

from dataclasses import dataclass

# Real-world endpoints
BENGALURU = (12.9716, 77.5946)
MYSURU = (12.2958, 76.6394)

# Grid resolution. 12 columns x 8 rows is enough to show meaningful
# rerouting without making the search space huge.
GRID_COLS = 12
GRID_ROWS = 8


@dataclass(frozen=True)
class Node:
    row: int
    col: int
    lat: float
    lon: float

    @property
    def id(self) -> str:
        return f"{self.row}-{self.col}"


def build_grid() -> dict[str, Node]:
    """
    Builds a GRID_ROWS x GRID_COLS lattice of Nodes spanning a bounding
    box around the Bengaluru -> Mysuru corridor.
    """
    lat0, lon0 = BENGALURU
    lat1, lon1 = MYSURU

    lat_min, lat_max = sorted([lat0, lat1])
    lon_min, lon_max = sorted([lon0, lon1])

    # Pad the bounding box a bit so detour routes have room to exist
    # outside the dead-straight line between the two cities.
    lat_pad = (lat_max - lat_min) * 0.35
    lon_pad = (lon_max - lon_min) * 0.35
    lat_min -= lat_pad
    lat_max += lat_pad
    lon_min -= lon_pad
    lon_max += lon_pad

    nodes: dict[str, Node] = {}
    for r in range(GRID_ROWS):
        for c in range(GRID_COLS):
            lat = lat_max - (r / (GRID_ROWS - 1)) * (lat_max - lat_min)
            lon = lon_min + (c / (GRID_COLS - 1)) * (lon_max - lon_min)
            node = Node(row=r, col=c, lat=lat, lon=lon)
            nodes[node.id] = node
    return nodes


def nearest_node(nodes: dict[str, Node], lat: float, lon: float) -> Node:
    """Finds the grid node closest to a given real-world coordinate."""
    return min(
        nodes.values(),
        key=lambda n: (n.lat - lat) ** 2 + (n.lon - lon) ** 2,
    )


def neighbors(node: Node) -> list[tuple[int, int]]:
    """8-directional neighbors (includes diagonals) within grid bounds."""
    deltas = [(-1, -1), (-1, 0), (-1, 1),
              (0, -1),           (0, 1),
              (1, -1),  (1, 0),  (1, 1)]
    result = []
    for dr, dc in deltas:
        r, c = node.row + dr, node.col + dc
        if 0 <= r < GRID_ROWS and 0 <= c < GRID_COLS:
            result.append((r, c))
    return result
