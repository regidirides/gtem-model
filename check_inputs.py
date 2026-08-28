"""Check a city's input folder BEFORE running a simulation.

    python check_inputs.py Chimbote_Zona1

Reports what GTEM will find: missing layers, wrong coordinate system, missing
attributes, how connected the road network is, and how many starting points can
actually reach a safe zone. Running this first turns a confusing mid-simulation
failure into a checklist.

Exit codes: 0 = usable, 1 = problems that will spoil results, 2 = cannot run.
"""
from __future__ import annotations

import sys
from pathlib import Path

# Library modules and the simulation engine live in src/.
sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

REQUIRED_LAYERS = {
    "zone boundary": "{zone}.shp",
    "road network": "rutas_{zone}.shp",
    "intersections": "puntos_{zone}.shp",
    "census blocks": "manzanas_{zone}.shp",
}

REQUIRED_FIELDS = {
    "rutas_{zone}.shp": ["start_node", "end_node", "cost", "lanes"],
    "puntos_{zone}.shp": ["fid", "is_shelter"],
}

POPULATION_FIELDS = ["T_TOTAL", "Population", "POP"]

OK, WARN, FAIL = "  [ OK ]", "  [WARN]", "  [FAIL]"


def check_zone(zone: str) -> int:
    import geopandas as gpd

    folder = BASE_DIR / "data" / zone
    print(f"Checking {folder}\n")
    if not folder.is_dir():
        print(f"{FAIL} folder does not exist")
        return 2

    problems, warnings = 0, 0

    # --- layers present -----------------------------------------------------
    layers: dict[str, Path] = {}
    for label, pattern in REQUIRED_LAYERS.items():
        path = folder / pattern.format(zone=zone)
        if path.is_file():
            print(f"{OK} {label:<16} {path.name}")
            layers[pattern] = path
        else:
            print(f"{FAIL} {label:<16} missing: {path.name}")
            problems += 1
    if problems:
        print(f"\n{problems} required layer(s) missing. GTEM cannot run.")
        return 2

    # --- coordinate reference system ---------------------------------------
    print()
    for pattern, path in layers.items():
        frame = gpd.read_file(path)
        crs = frame.crs
        if crs is None:
            print(f"{FAIL} {path.name}: no CRS. GTEM needs a projected, metric CRS.")
            problems += 1
        elif crs.is_geographic:
            print(f"{FAIL} {path.name}: geographic CRS ({crs.name}). Distances "
                  "would be in DEGREES. Reproject to UTM and re-export.")
            problems += 1
        else:
            print(f"{OK} {path.name:<34} CRS {crs.name}")

    # --- attributes ---------------------------------------------------------
    print()
    for pattern, fields in REQUIRED_FIELDS.items():
        path = folder / pattern.format(zone=zone)
        columns = {c.lower() for c in gpd.read_file(path).columns}
        for field in fields:
            if field.lower() in columns:
                print(f"{OK} {path.name}: has '{field}'")
            else:
                print(f"{FAIL} {path.name}: missing '{field}'")
                problems += 1

    blocks = gpd.read_file(folder / f"manzanas_{zone}.shp")
    found = [f for f in POPULATION_FIELDS if f in blocks.columns]
    if found:
        field = found[0]
        values = blocks[field].apply(
            lambda v: float(v) if str(v).replace(".", "", 1).lstrip("-").isdigit() else None)
        blank = int(values.isna().sum())
        print(f"{OK} census blocks: population field '{field}', "
              f"total {values.sum():,.0f} over {len(blocks)} blocks")
        if blank:
            print(f"{WARN} {blank} block(s) have a missing or non-numeric '{field}'; "
                  "they will receive no population")
            warnings += 1
    else:
        print(f"{WARN} census blocks: none of {POPULATION_FIELDS} found. "
              "Population will be spread UNIFORMLY, ignoring where people live.")
        warnings += 1

    # --- network connectivity ----------------------------------------------
    print()
    import networkx as nx

    roads = gpd.read_file(folder / f"rutas_{zone}.shp")
    points = gpd.read_file(folder / f"puntos_{zone}.shp")
    graph = nx.Graph()
    for _, row in roads.iterrows():
        try:
            u, v, w = int(float(row["start_node"])), int(float(row["end_node"])), float(row["cost"])
        except (TypeError, ValueError):
            continue
        if u != v:
            graph.add_edge(u, v, weight=w)

    id_field = "fid" if "fid" in points.columns else points.columns[0]
    safe = {int(float(r[id_field])) for _, r in points.iterrows()
            if str(r.get("is_shelter", 0)) not in ("", "0", "0.0", "None")}
    origins = {int(float(r[id_field])) for _, r in points.iterrows()} - safe

    print(f"{OK} network: {graph.number_of_nodes()} nodes, "
          f"{graph.number_of_edges()} links, {len(safe)} safe zone(s)")
    if not safe:
        print(f"{FAIL} no safe zones: no point has is_shelter = 1. Nobody can evacuate.")
        return 2

    components = nx.number_connected_components(graph)
    if components > 1:
        print(f"{WARN} network is in {components} disconnected pieces")
        warnings += 1

    reachable = set()
    for source in (s for s in safe if s in graph):
        reachable |= nx.node_connected_component(graph, source)
    unroutable = [o for o in origins if o not in reachable]
    share = len(unroutable) / max(len(origins), 1) * 100
    tag = FAIL if share > 25 else (WARN if unroutable else OK)
    print(f"{tag} {len(unroutable)} of {len(origins)} starting points "
          f"({share:.1f}%) cannot reach ANY safe zone")
    if unroutable:
        warnings += 1

    short = [float(c) for c in roads["cost"] if str(c).replace(".", "", 1).isdigit()
             and float(c) < 1.0]
    if short:
        print(f"{WARN} {len(short)} link(s) shorter than 1 m "
              f"(min {min(short):.3f} m) will produce implausible densities")
        warnings += 1

    print()
    if problems:
        print(f"{problems} problem(s) will prevent or invalidate a run.")
        return 1
    if warnings:
        print(f"Usable, with {warnings} warning(s). Read them before trusting results.")
        return 0
    print("No problems found. This folder is ready.")
    return 0


def main() -> int:
    if len(sys.argv) != 2:
        available = sorted(p.name for p in (BASE_DIR / "data").iterdir() if p.is_dir())
        print(__doc__)
        print("Available zones:")
        for zone in available:
            print(f"  {zone}")
        return 2
    return check_zone(sys.argv[1])


if __name__ == "__main__":
    sys.exit(main())
