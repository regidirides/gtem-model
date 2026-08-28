"""Dose-response of evacuation outcome to road capacity.

    python tools/plot_capacity_response.py out_stem Outputs/Sweep_10 Outputs/Sweep_05 ...

Each folder is a run that differs only in `capacity_multiplier`. Three panels:
what reaches safety, how crowded the streets get, and how fast people walk.
"""
from __future__ import annotations

import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import pandas as pd  # noqa: E402

INK, RED, BLUE, AMBER = "#111111", "#c62828", "#1565c0", "#f0a500"


def main() -> int:
    if len(sys.argv) < 3:
        print(__doc__)
        return 2
    stem, folders = sys.argv[1], sys.argv[2:]

    rows = []
    for folder in folders:
        path = Path(folder)
        summary = pd.read_csv(path / "Run_Summary.csv").iloc[0]
        config = (path / "resolved_config.txt").read_text(encoding="utf-8")
        multiplier = next(
            float(line.split("=")[1]) for line in config.splitlines()
            if line.strip().startswith("capacity_multiplier"))
        congestion = pd.read_csv(path / "Report5_Congestion.csv")
        speeds = pd.read_csv(path / "Report2_Speeds.csv")
        moving = speeds["Speed_Adults"][speeds["Speed_Adults"] > 0]
        rows.append({
            "multiplier": multiplier,
            "pct": float(summary["Pct_Evacuated"]),
            "evacuated": int(summary["Evacuated_Before_ETA"]),
            "caught": int(summary["Caught_In_Transit"]),
            "density": congestion["Peak_Density"].mean(),
            "congested": int((congestion["Peak_Density"] > 0.3).sum()),
            "speed": moving.mean(),
        })
    data = pd.DataFrame(rows).sort_values("multiplier")
    x = data["multiplier"] * 100

    figure, axes = plt.subplots(1, 3, figsize=(14.5, 4.9))

    axes[0].plot(x, data["pct"], "o-", color=INK, linewidth=2.2, markersize=7)
    for _, r in data.iterrows():
        axes[0].annotate(f"{r['pct']:.1f}%", (r["multiplier"] * 100, r["pct"]),
                         textcoords="offset points", xytext=(0, 10),
                         ha="center", fontsize=9.5)
    axes[0].set_ylabel("Evacuated before the wave (%)")
    axes[0].set_title("Outcome", fontsize=12, fontweight="bold", loc="left")
    axes[0].set_ylim(0, 75)

    axes[1].plot(x, data["density"], "o-", color=RED, linewidth=2.2, markersize=7)
    axes[1].axhline(0.3, color=AMBER, linestyle="--", linewidth=1.3)
    axes[1].text(x.max() * 0.98, 0.34, "free-flow threshold 0.3", fontsize=8.5,
                 color=AMBER, ha="right")
    axes[1].axhline(3.0, color=RED, linestyle=":", linewidth=1.3)
    axes[1].text(x.max() * 0.98, 3.2, "crush 3.0", fontsize=8.5, color=RED,
                 ha="right")
    axes[1].set_ylabel("Mean peak density (people/m²)")
    axes[1].set_title("Crowding", fontsize=12, fontweight="bold", loc="left")

    axes[2].plot(x, data["speed"], "o-", color=BLUE, linewidth=2.2, markersize=7)
    axes[2].axhline(1.33, color="#888888", linestyle="--", linewidth=1.3)
    axes[2].text(x.max() * 0.98, 1.35, "free flow 1.33 m/s", fontsize=8.5,
                 color="#888888", ha="right")
    axes[2].set_ylabel("Mean adult walking speed (m/s)")
    axes[2].set_title("Speed", fontsize=12, fontweight="bold", loc="left")
    axes[2].set_ylim(0.6, 1.42)

    for axis in axes:
        axis.set_xlabel("Road capacity (% of normal width)")
        axis.grid(alpha=0.25)
        axis.set_xscale("log")
        axis.set_xticks(list(x))
        axis.set_xticklabels([f"{v:g}" for v in x])
        axis.minorticks_off()

    figure.suptitle("Effect of road capacity on evacuation — Chimbote Zona 1, "
                    "17,261 people, all else identical",
                    fontsize=13.5, fontweight="bold", x=0.02, ha="left")
    figure.text(0.02, 0.015,
                "capacity_multiplier scales the usable width of every road. "
                "Population, departure times, routes, tsunami arrival and random "
                "seed are the same in all five runs.",
                fontsize=8.5, color="#555555")
    figure.subplots_adjust(left=0.06, right=0.985, top=0.83, bottom=0.20,
                           wspace=0.28)
    for suffix in ("png", "pdf"):
        figure.savefig(f"{stem}.{suffix}", dpi=200)
    print(f"  {stem}.png / .pdf")
    print(data.to_string(index=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
