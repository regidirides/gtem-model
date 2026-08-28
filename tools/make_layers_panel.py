"""Draw the three input layers of a study area as one panel, for the demo video.

    python tools/make_layers_panel.py Chimbote_Zona1 layers.png

Reads the shapefiles directly, so the picture cannot drift from the data.
"""
from __future__ import annotations

import sys
from pathlib import Path

import geopandas as gpd
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
BG = "#121214"


def main() -> int:
    if len(sys.argv) != 3:
        print(__doc__)
        return 2
    zone, out = sys.argv[1], sys.argv[2]
    folder = ROOT / "data" / zone

    roads = gpd.read_file(folder / f"rutas_{zone}.shp")
    points = gpd.read_file(folder / f"puntos_{zone}.shp")
    blocks = gpd.read_file(folder / f"manzanas_{zone}.shp")
    population = next((c for c in ("T_TOTAL", "Population", "POP")
                       if c in blocks.columns), None)

    figure, axes = plt.subplots(1, 3, figsize=(15, 5.6), facecolor=BG)
    for axis in axes:
        axis.set_facecolor(BG)
        axis.set_xticks([]), axis.set_yticks([])
        axis.set_aspect("equal")
        for spine in axis.spines.values():
            spine.set_visible(False)

    roads.plot(ax=axes[0], color="#4da3ff", linewidth=0.45)
    axes[0].set_title(f"Road network\nrutas_{zone}.shp  ({len(roads):,} segments)",
                      color="white", fontsize=12)

    blocks.plot(ax=axes[1], column=population, cmap="magma",
                linewidth=0.15, edgecolor="#333333")
    axes[1].set_title(
        f"Census blocks by population\nmanzanas_{zone}.shp  ({population})",
        color="white", fontsize=12)

    roads.plot(ax=axes[2], color="#2f2f36", linewidth=0.35)
    shelters = (points[points["is_shelter"] == 1]
                if "is_shelter" in points.columns else points.iloc[:0])
    shelters.plot(ax=axes[2], color="#4cc36e", marker="*", markersize=340,
                  edgecolor="white", linewidth=0.8)
    axes[2].set_title(
        f"Safe zones\nis_shelter = 1  ({len(shelters)} of {len(points):,} points)",
        color="white", fontsize=12)

    figure.tight_layout()
    figure.savefig(out, dpi=110, facecolor=BG)
    print(f"  {out}: {len(roads):,} segments, {len(blocks)} blocks, "
          f"{len(shelters)} safe zones")
    return 0


if __name__ == "__main__":
    sys.exit(main())
