"""Side-by-side animation of TUNAMI-EVAC1 and GTEM on the same scenario.

    python tools/build_side_by_side.py --tunami t.npz --gtem g.npz \
        --tsunami-dir <TsunamiDB> --output side_by_side.mp4

The two models use different world coordinates, so each panel is drawn in its
own extent; they cover the same ground. Time is the common axis: every output
frame picks the capture nearest that minute in each model.
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
GREY, BLACK, GREEN, WATER = "#8a8a8a", "#111111", "#2e7d32", "#2f7fd0"
#: The ancestor starts reading inundation grids at this tick, and the file
#: index is 50000 + tick. Both come from the model source.
TSUNAMI_FIRST_TICK, TSUNAMI_FILE_OFFSET = 3900, 50000


def offsets(counts):
    return np.concatenate([[0], np.cumsum(counts)]).astype(int)


def load_asc(path: Path):
    """Read an ESRI ASCII grid, returning (values, nodata)."""
    header, values = {}, []
    with open(path) as fh:
        for _ in range(6):
            key, value = fh.readline().split()
            header[key.lower()] = float(value)
        for line in fh:
            values.extend(float(v) for v in line.split())
    rows, cols = int(header["nrows"]), int(header["ncols"])
    return np.asarray(values).reshape(rows, cols), header["nodata_value"]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tunami", required=True)
    parser.add_argument("--gtem", required=True)
    parser.add_argument("--tsunami-dir", default="")
    parser.add_argument("--output", default="side_by_side.mp4")
    parser.add_argument("--seconds", type=float, default=75.0)
    parser.add_argument("--workdir", default="_sbs")
    args = parser.parse_args()

    t = np.load(args.tunami)
    g = np.load(args.gtem)

    t_min = t["ticks"] / 60.0
    t_off, t_xy = offsets(t["counts"]), t["xy"]
    t_total = float(t["total"])
    t_safe = t["safe"]

    g_dt = float(g["dt"])
    g_min = g["tick"] * g_dt / 60.0
    g_breeds = ("adults", "elderly", "children")
    g_off = {b: offsets(g[f"{b}_counts"]) for b in g_breeds}
    g_arr = {b: g[f"{b}_xyz"] for b in g_breeds}
    g_safe = g["evacuated"]
    g_total = sum(int(g[f"{b}_counts"][0]) for b in g_breeds)

    span = max(t_min[-1], g_min[-1])
    n_frames = int(args.seconds * FPS)

    figure = plt.figure(figsize=(W / 100, H / 100), dpi=100, facecolor=PAPER)
    left = figure.add_axes([0.025, 0.30, 0.44, 0.55])
    right = figure.add_axes([0.525, 0.30, 0.44, 0.55])
    curve = figure.add_axes([0.075, 0.075, 0.86, 0.15])

    for axis in (left, right):
        axis.set_facecolor(PAPER)
        axis.set_xticks([]), axis.set_yticks([]), axis.set_aspect("equal")
        for spine in axis.spines.values():
            spine.set_edgecolor("#dddddd")

    # --- static backgrounds ------------------------------------------------
    streets = t["static_street"]
    if len(streets):
        left.scatter(streets[:, 0], streets[:, 1], s=0.8, c="#e2e2e2",
                     marker="s", zorder=1)
    for name, colour in (("static_exit", GREEN), ("static_teb", GREEN)):
        pts = t[name]
        if len(pts):
            left.scatter(pts[:, 0], pts[:, 1], s=260, marker="*", c=colour,
                         edgecolors="white", linewidths=0.8, zorder=6)

    edges, nodes = g["edges"], g["nodes"]
    if len(edges):
        right.add_collection(LineCollection(
            [[(e[0], e[1]), (e[2], e[3])] for e in edges],
            colors="#e2e2e2", linewidths=0.6, zorder=1))
    safe_nodes = nodes[nodes[:, 2] == 1] if len(nodes) else np.empty((0, 3))
    if len(safe_nodes):
        right.scatter(safe_nodes[:, 0], safe_nodes[:, 1], s=260, marker="*",
                      c=GREEN, edgecolors="white", linewidths=0.8, zorder=6)

    water = left.imshow(np.zeros((1, 1)), cmap="Blues", alpha=0.0, zorder=2)
    t_dots = left.scatter([], [], s=2.2, c=BLACK, zorder=4)
    g_dots = right.scatter([], [], s=2.2, c=BLACK, zorder=4)

    for axis, pts in ((left, streets), (right, nodes)):
        if len(pts):
            pad = 0.03 * (pts[:, 0].max() - pts[:, 0].min() + 1)
            axis.set_xlim(pts[:, 0].min() - pad, pts[:, 0].max() + pad)
            axis.set_ylim(pts[:, 1].min() - pad, pts[:, 1].max() + pad)

    figure.text(0.5, 0.965, "Arahama, 11 March 2011 — the same scenario in two models",
                ha="center", fontsize=17, fontweight="bold", color=INK)
    figure.text(0.5, 0.935,
                "2,271 people on foot · matched departure times · wave at 67 min",
                ha="center", fontsize=11, color=MUTED)
    figure.text(0.245, 0.885, "TUNAMI-EVAC1 (2012)", ha="center",
                fontsize=13, fontweight="bold", color=GREY)
    figure.text(0.745, 0.885, "GTEM v1.0.0", ha="center",
                fontsize=13, fontweight="bold", color=BLACK)

    clock = figure.text(0.5, 0.885, "", ha="center", fontsize=26,
                        fontweight="bold", family="monospace", color=INK)
    t_stat = figure.text(0.245, 0.265, "", ha="center", fontsize=12,
                         family="monospace", color=GREY)
    g_stat = figure.text(0.745, 0.265, "", ha="center", fontsize=12,
                         family="monospace", color=BLACK)

    curve.plot(t_min, t_safe / t_total * 100, color=GREY, linewidth=1.8,
               label="TUNAMI-EVAC1")
    curve.plot(g_min, g_safe / g_total * 100, color=BLACK, linewidth=1.8,
               label="GTEM v1.0.0")
    curve.axhline(90, color=INK, linestyle="--", linewidth=1.1)
    curve.text(0.4, 92, "observed 2011: 90%", fontsize=8.5, color=INK)
    curve.set_xlim(0, span), curve.set_ylim(0, 104)
    curve.set_xlabel("Minutes since the earthquake", fontsize=10)
    curve.set_ylabel("Evacuated (%)", fontsize=10)
    curve.grid(alpha=0.25)
    curve.legend(loc="upper left", fontsize=9, framealpha=0.95)
    marker = curve.axvline(0, color="#c62828", linewidth=1.6)

    tsunami_dir = Path(args.tsunami_dir) if args.tsunami_dir else None
    work = Path(args.workdir)
    shutil.rmtree(work, ignore_errors=True)
    work.mkdir(parents=True)

    for f in range(n_frames):
        minute = f / max(1, n_frames - 1) * span
        i = int(np.searchsorted(t_min, minute).clip(0, len(t_min) - 1))
        j = int(np.searchsorted(g_min, minute).clip(0, len(g_min) - 1))

        t_dots.set_offsets(t_xy[t_off[i]:t_off[i + 1]]
                           if t_off[i + 1] > t_off[i] else np.empty((0, 2)))
        parts = [g_arr[b][g_off[b][j]:g_off[b][j + 1]][:, :2] for b in g_breeds
                 if g_off[b][j + 1] > g_off[b][j]]
        g_dots.set_offsets(np.vstack(parts) if parts else np.empty((0, 2)))

        tick = int(round(t_min[i] * 60))
        if tsunami_dir and tick >= TSUNAMI_FIRST_TICK:
            grid_file = tsunami_dir / f"out{TSUNAMI_FILE_OFFSET + tick}.asc"
            if grid_file.is_file():
                grid, nodata = load_asc(grid_file)
                flooded = np.where((grid > 0) & (grid != nodata), grid, np.nan)
                water.set_data(flooded)
                water.set_extent([0, grid.shape[1] - 1, -(grid.shape[0] - 1), 0])
                water.set_clim(0, 8)
                water.set_alpha(0.55)

        clock.set_text(f"{minute:5.1f} min")
        ts, gs = float(t_safe[i]), float(g_safe[j])
        t_stat.set_text(f"safe {ts:5.0f} / {t_total:.0f}   ({ts/t_total*100:4.1f}%)")
        g_stat.set_text(f"safe {gs:5.0f} / {g_total:.0f}   ({gs/g_total*100:4.1f}%)")
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
