"""Derive a reduced-capacity variant of a study area.

    python tools/make_reduced_capacity_zone.py Chimbote_Zona1 Chimbote_Zona1_lowcap \
        --min-lanes 3 --factor 0.25

Copies a zone and reduces the `lanes` attribute on the roads that currently have
`--min-lanes` or more, leaving every other layer and every geometry untouched.

WHY LANES, AND WHY NOT REMOVE ROADS
    GTEM computes crowd density as agents / (lanes x road_width x length), so
    `lanes` is the per-road capacity. Reducing it narrows a street without
    changing the network, so routes, travel distances and reachability are
    identical and the only thing that varies is congestion. Deleting links --
    what the supplied `_colapso` zones do -- also changes connectivity and can
    strand people, which conflates two effects.

    `capacity_multiplier` in the configuration scales every road at once. Use
    this tool when the disruption is confined to particular streets.
"""
from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path

import geopandas as gpd

ROOT = Path(__file__).resolve().parent.parent


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("source")
    parser.add_argument("target")
    parser.add_argument("--min-lanes", type=int, default=3,
                        help="Reduce roads having at least this many lanes.")
    parser.add_argument("--factor", type=float, default=0.25,
                        help="Multiply their lane count by this, floor 1.")
    parser.add_argument("--from-congestion", default="",
                        help="Report5_Congestion.csv from a baseline run. Targets "
                             "the busiest evacuation corridors instead of using "
                             "--min-lanes, which mostly hits roads nobody uses.")
    parser.add_argument("--top", type=int, default=300,
                        help="With --from-congestion: how many corridors to narrow.")
    args = parser.parse_args()

    src = ROOT / "data" / args.source
    dst = ROOT / "data" / args.target
    if not src.is_dir():
        print(f"No such zone: {src}")
        return 2
    if dst.exists():
        shutil.rmtree(dst)
    dst.mkdir(parents=True)

    for path in sorted(src.iterdir()):
        if not path.is_file():
            continue
        new_name = path.name.replace(args.source, args.target)
        shutil.copy2(path, dst / new_name)

    roads_path = dst / f"rutas_{args.target}.shp"
    roads = gpd.read_file(roads_path)
    if "lanes" not in roads.columns:
        print("The road layer has no 'lanes' attribute; nothing to reduce.")
        return 2

    original = roads["lanes"].astype(float)
    if args.from_congestion:
        import pandas as pd
        busiest = pd.read_csv(args.from_congestion).nlargest(args.top, "Exposure")
        wanted = {(int(float(a)), int(float(b)))
                  for a, b in zip(busiest["start_node"], busiest["end_node"])}
        pairs = [(int(float(a)), int(float(b)))
                 for a, b in zip(roads["start_node"], roads["end_node"])]
        target = pd.Series([p in wanted or p[::-1] in wanted for p in pairs],
                           index=roads.index)
    else:
        target = original >= args.min_lanes
    reduced = original.copy()
    reduced[target] = (original[target] * args.factor).apply(
        lambda v: max(1, int(round(v))))
    roads["lanes"] = reduced.astype(int).astype(str)
    roads.to_file(roads_path)

    before = float((original * roads["cost"].astype(float)).sum())
    after = float((reduced * roads["cost"].astype(float)).sum())
    print(f"  {args.source} -> {args.target}")
    print(f"    roads reduced      : {int(target.sum()):,} of {len(roads):,} "
          f"({target.mean()*100:.1f}%)")
    print(f"    lane-metres before : {before:,.0f}")
    print(f"    lane-metres after  : {after:,.0f}  "
          f"({(after/before-1)*100:+.1f}%)")
    print(f"    geometry, nodes, blocks: unchanged")
    return 0


if __name__ == "__main__":
    sys.exit(main())
