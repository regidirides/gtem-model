"""Generate synthetic study areas whose correct answer is known by hand.

Two zones:

**Synthetic_Corridor** — the scale-sanity case. Two straight 1,000 m corridors,
one running east-west and one north-south, each ending at a safe zone. An adult
walking at the free-flow speed covers 1,000 m in 1000 / 1.33 = 751.88 s
= 12.53 min. Any error in the metres-per-patch scale, the timestep, or the
movement loop shows up immediately as a departure from that number, and the two
corridors must agree with each other or the world is anisotropic.

**Synthetic_Broken** — a deliberately defective folder for the warning tests: no
population attribute, an isolated network fragment, and a sub-metre link. It
exists so the warning tests assert on a KNOWN defect rather than relying on the
real Chimbote data happening to be flawed.

These zones carry no third-party data, so they can be redistributed freely and
give a new user something that runs immediately from a fresh clone.

    python tools/make_synthetic_zone.py
"""

from __future__ import annotations

from pathlib import Path

import geopandas as gpd
from shapely.geometry import LineString, Point, Polygon

CRS = "EPSG:32717"          # UTM 17S, metric, same family as the Chimbote data
X0, Y0 = 500_000.0, 9_000_000.0
SPACING = 50.0              # metres between intersections
CORRIDOR_LENGTH = 1000.0    # metres from the first node to the safe zone
BLOCK_HALF = 1.0            # half-width of a census block, metres

ROOT = Path(__file__).resolve().parent.parent


def corridor(start, direction, count, first_id):
    """Nodes and links along a straight line. Returns (nodes, links, next_id)."""
    nodes, links = [], []
    for step in range(count):
        node_id = first_id + step
        x = start[0] + direction[0] * SPACING * step
        y = start[1] + direction[1] * SPACING * step
        nodes.append({"fid": node_id, "is_shelter": 0, "name": "",
                      "geometry": Point(x, y)})
        if step:
            previous = nodes[step - 1]["geometry"]
            links.append({"start_node": node_id - 1, "end_node": node_id,
                          "cost": SPACING, "lanes": 2,
                          "geometry": LineString([previous, (x, y)])})
    return nodes, links, first_id + count


def square(centre, half):
    x, y = centre
    return Polygon([(x - half, y - half), (x + half, y - half),
                    (x + half, y + half), (x - half, y + half)])


def write(folder: Path, zone: str, nodes, links, blocks, extent):
    folder.mkdir(parents=True, exist_ok=True)
    gpd.GeoDataFrame([{"geometry": square(extent[0], extent[1])}],
                     crs=CRS).to_file(folder / f"{zone}.shp")
    gpd.GeoDataFrame(nodes, crs=CRS).to_file(folder / f"puntos_{zone}.shp")
    gpd.GeoDataFrame(links, crs=CRS).to_file(folder / f"rutas_{zone}.shp")
    gpd.GeoDataFrame(blocks, crs=CRS).to_file(folder / f"manzanas_{zone}.shp")
    print(f"  {zone}: {len(nodes)} nodes, {len(links)} links, "
          f"{len(blocks)} blocks -> {folder}")


def build_corridor_zone():
    """Two 1,000 m corridors, one east-west, one north-south."""
    count = int(CORRIDOR_LENGTH / SPACING) + 1     # 21 nodes, 20 gaps

    east_start = (X0 + 100, Y0 + 200)
    east_nodes, east_links, next_id = corridor(east_start, (1, 0), count, 1)
    east_nodes[-1].update(is_shelter=1, name="East safe zone")

    north_start = (X0 + 1200, Y0 + 200)
    north_nodes, north_links, _ = corridor(north_start, (0, 1), count, next_id)
    north_nodes[-1].update(is_shelter=1, name="North safe zone")

    blocks = [
        {"T_TOTAL": 100, "corridor": "east",
         "geometry": square(east_start, BLOCK_HALF)},
        {"T_TOTAL": 100, "corridor": "north",
         "geometry": square(north_start, BLOCK_HALF)},
    ]
    write(ROOT / "data" / "Synthetic_Corridor", "Synthetic_Corridor",
          east_nodes + north_nodes, east_links + north_links, blocks,
          ((X0 + 700, Y0 + 700), 700))


def build_broken_zone():
    """Deliberately defective: no population, an island, a sub-metre link."""
    nodes, links, next_id = corridor((X0 + 100, Y0 + 200), (1, 0), 11, 1)
    nodes[-1].update(is_shelter=1, name="Only safe zone")

    # An island: connected to itself, reaching nothing.
    island, island_links, next_id = corridor((X0 + 100, Y0 + 900), (1, 0), 5, next_id)

    # A sub-metre link, which produces an implausible density from one agent.
    tiny_a, tiny_b = next_id, next_id + 1
    nodes += [
        {"fid": tiny_a, "is_shelter": 0, "name": "",
         "geometry": Point(X0 + 300, Y0 + 200)},
        {"fid": tiny_b, "is_shelter": 0, "name": "",
         "geometry": Point(X0 + 300.2, Y0 + 200)},
    ]
    links.append({"start_node": tiny_a, "end_node": tiny_b, "cost": 0.2,
                  "lanes": 1,
                  "geometry": LineString([(X0 + 300, Y0 + 200),
                                          (X0 + 300.2, Y0 + 200)])})

    # Blocks with NO population attribute at all.
    blocks = [
        {"note": "on-network", "geometry": square((X0 + 100, Y0 + 200), BLOCK_HALF)},
        {"note": "on-island", "geometry": square((X0 + 100, Y0 + 900), BLOCK_HALF)},
    ]
    write(ROOT / "data" / "Synthetic_Broken", "Synthetic_Broken",
          nodes + island, links + island_links, blocks,
          ((X0 + 400, Y0 + 550), 600))


def build_no_safe_zone():
    """A network where no point is flagged as a safe zone: nobody can evacuate."""
    nodes, links, _ = corridor((X0 + 100, Y0 + 200), (1, 0), 6, 1)
    blocks = [{"T_TOTAL": 50, "geometry": square((X0 + 100, Y0 + 200), BLOCK_HALF)}]
    write(ROOT / "data" / "Synthetic_NoSafeZone", "Synthetic_NoSafeZone",
          nodes, links, blocks, ((X0 + 250, Y0 + 300), 350))


if __name__ == "__main__":
    print("Generating synthetic zones...")
    build_corridor_zone()
    build_broken_zone()
    build_no_safe_zone()
    print("\nExpected walking time for either corridor:")
    print(f"  {CORRIDOR_LENGTH:.0f} m / 1.33 m/s = "
          f"{CORRIDOR_LENGTH / 1.33:.2f} s = {CORRIDOR_LENGTH / 1.33 / 60:.4f} min")
