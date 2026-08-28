"""Side-by-side animation of two GTEM runs that differ only in road capacity.

    python tools/build_capacity_video.py --left frames_a.npz --right frames_b.npz \
        --left-label "All roads" --right-label "Capacity 25%" --output capacity.mp4

Both captures must come from the same study area and the same population, so the
only visible difference is congestion. Agents are coloured by whether they have
started walking; the panel titles carry the headline result.
"""
from __future__ import annotations

import argparse
import shutil
import subprocess
from pathlib import Path

import matplotlib
import numpy as np

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.collections import LineCollection  # noqa: E402

FPS, W, H = 24, 1600, 900
PAPER, INK, MUTED = "#ffffff", "#1a1a1a", "#8a8a8a"
MOVING, WAITING, GREEN, RED = "#1565c0", "#f0a500", "#2e7d32", "#c62828"
BREEDS = ("adults", "elderly", "children")


def offsets(counts):
    return np.concatenate([[0], np.cumsum(counts)]).astype(int)


def prepare(data):
    return {"minutes": data["tick"] * float(data["dt"]) / 60.0,
            "evacuated": data["evacuated"],
            "off": {b: offsets(data[f"{b}_counts"]) for b in BREEDS},
            "arr": {b: data[f"{b}_xyz"] for b in BREEDS},
            "total": sum(int(data[f"{b}_counts"][0]) for b in BREEDS),
            "nodes": data["nodes"], "edges": data["edges"],
            "eta": float(data["tsunami_eta"])}


def draw_static(axis, case):
    axis.set_facecolor(PAPER)
    axis.set_xticks([]), axis.set_yticks([]), axis.set_aspect("equal")
    for spine in axis.spines.values():
        spine.set_edgecolor("#dddddd")
    if len(case["edges"]):
        axis.add_collection(LineCollection(
            [[(e[0], e[1]), (e[2], e[3])] for e in case["edges"]],
            colors="#e4e4e4", linewidths=0.5, zorder=1))
    safe = case["nodes"][case["nodes"][:, 2] == 1]
    if len(safe):
        axis.scatter(safe[:, 0], safe[:, 1], s=210, marker="*", c=GREEN,
                     edgecolors="white", linewidths=0.8, zorder=6)
    pts = case["nodes"]
    pad = 0.03 * (pts[:, 0].max() - pts[:, 0].min() + 1)
    axis.set_xlim(pts[:, 0].min() - pad, pts[:, 0].max() + pad)
    axis.set_ylim(pts[:, 1].min() - pad, pts[:, 1].max() + pad)


def positions(case, j):
    move, wait = [], []
    for b in BREEDS:
        a, z = case["off"][b][j], case["off"][b][j + 1]
        if z <= a:
            continue
        block = case["arr"][b][a:z]
        ready = block[:, 2] > 0
        move.append(block[ready][:, :2])
        wait.append(block[~ready][:, :2])
    return (np.vstack(move) if move else np.empty((0, 2)),
            np.vstack(wait) if wait else np.empty((0, 2)))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--left", required=True)
    parser.add_argument("--right", required=True)
    parser.add_argument("--left-label", default="All roads")
    parser.add_argument("--right-label", default="Reduced capacity")
    parser.add_argument("--output", default="capacity.mp4")
    parser.add_argument("--seconds", type=float, default=55.0)
    parser.add_argument("--workdir", default="_cap")
    args = parser.parse_args()

    a = prepare(np.load(args.left))
    b = prepare(np.load(args.right))
    span = max(a["minutes"][-1], b["minutes"][-1])
    n_frames = int(args.seconds * FPS)

    figure = plt.figure(figsize=(W / 100, H / 100), dpi=100, facecolor=PAPER)
    left = figure.add_axes([0.025, 0.29, 0.44, 0.56])
    right = figure.add_axes([0.525, 0.29, 0.44, 0.56])
    curve = figure.add_axes([0.075, 0.095, 0.86, 0.13])
    draw_static(left, a), draw_static(right, b)

    l_move = left.scatter([], [], s=2.4, c=MOVING, zorder=4)
    l_wait = left.scatter([], [], s=2.4, c=WAITING, zorder=3)
    r_move = right.scatter([], [], s=2.4, c=MOVING, zorder=4)
    r_wait = right.scatter([], [], s=2.4, c=WAITING, zorder=3)

    figure.text(0.5, 0.965, "Road capacity — the same evacuation, twice",
                ha="center", fontsize=17, fontweight="bold", color=INK)
    figure.text(0.5, 0.933,
                f"Chimbote Zona 1 · {a['total']:,} people · identical population, "
                f"departure times and seed · wave at {a['eta']:.0f} min",
                ha="center", fontsize=10.5, color=MUTED)
    figure.text(0.245, 0.878, args.left_label, ha="center", fontsize=13,
                fontweight="bold", color=INK)
    figure.text(0.745, 0.878, args.right_label, ha="center", fontsize=13,
                fontweight="bold", color=RED)
    clock = figure.text(0.5, 0.876, "", ha="center", fontsize=24,
                        fontweight="bold", family="monospace", color=INK)
    l_stat = figure.text(0.245, 0.255, "", ha="center", fontsize=12,
                         family="monospace", color=INK)
    r_stat = figure.text(0.745, 0.255, "", ha="center", fontsize=12,
                         family="monospace", color=RED)
    # Bottom-left of the figure. Beside the counters it ran through the "safe
    # N / N" readout; under the subtitle it clipped the clock.
    figure.text(0.075, 0.012, "blue walking · amber not yet left · green safe zone",
                fontsize=9, color=MUTED)

    curve.plot(a["minutes"], a["evacuated"] / a["total"] * 100, color=INK,
               linewidth=1.9, label=args.left_label)
    curve.plot(b["minutes"], b["evacuated"] / b["total"] * 100, color=RED,
               linewidth=1.9, label=args.right_label)
    curve.set_xlim(0, span), curve.set_ylim(0, 100)
    curve.set_xlabel("Minutes since the earthquake", fontsize=10)
    curve.set_ylabel("Evacuated (%)", fontsize=10)
    curve.grid(alpha=0.25)
    curve.legend(loc="upper left", fontsize=9, framealpha=0.95)
    marker = curve.axvline(0, color="#666666", linewidth=1.4)

    work = Path(args.workdir)
    shutil.rmtree(work, ignore_errors=True)
    work.mkdir(parents=True)

    for f in range(n_frames):
        minute = f / max(1, n_frames - 1) * span
        i = int(np.searchsorted(a["minutes"], minute).clip(0, len(a["minutes"]) - 1))
        j = int(np.searchsorted(b["minutes"], minute).clip(0, len(b["minutes"]) - 1))
        m1, w1 = positions(a, i)
        m2, w2 = positions(b, j)
        l_move.set_offsets(m1), l_wait.set_offsets(w1)
        r_move.set_offsets(m2), r_wait.set_offsets(w2)
        clock.set_text(f"{minute:4.1f} min")
        for text, case, k in ((l_stat, a, i), (r_stat, b, j)):
            safe = float(case["evacuated"][k])
            text.set_text(f"safe {safe:6,.0f} / {case['total']:,}  "
                          f"({safe/case['total']*100:4.1f}%)")
        marker.set_xdata([minute, minute])
        figure.savefig(work / f"f{f:06d}.png", facecolor=PAPER)
    plt.close(figure)

    encoders = subprocess.run(["ffmpeg", "-hide_banner", "-encoders"],
                              capture_output=True, text=True).stdout
    codec = (["-c:v", "libx264", "-crf", "20"] if " libx264" in encoders
             else ["-c:v", "h264_videotoolbox", "-b:v", "6M"])
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-framerate", str(FPS),
                    "-i", str(work / "f%06d.png")] + codec
                   + ["-pix_fmt", "yuv420p", "-movflags", "+faststart",
                      args.output], check=True)
    shutil.rmtree(work, ignore_errors=True)
    print(f"  {args.output} — {n_frames/FPS:.0f} s, "
          f"{Path(args.output).stat().st_size/1e6:.1f} MB")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
