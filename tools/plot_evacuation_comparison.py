"""Cumulative evacuation curves from two models on the same study area.

    python tools/plot_evacuation_comparison.py out_stem \
        "Label A=Report1_Dynamics.csv[,Report2_Speeds.csv]" "Label B=..."

Giving a speeds CSV as well adds a lower panel of mean walking speed, which is
usually what explains any divergence between the curves.

Each CSV needs a time column in minutes and a cumulative-evacuated percentage.
Both the original model's schema (Time_Minutes, Pct_Evacuated) and GTEM's are
recognised, so curves from different generations of the model can be overlaid.
"""
from __future__ import annotations

import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import pandas as pd  # noqa: E402

COLOURS = ["#c62828", "#1565c0", "#2e7d32", "#f9a825"]
TIME_COLUMNS = ("Time_Minutes", "Minutes", "Time")
PERCENT_COLUMNS = ("Pct_Evacuated",)


def _series(path: Path) -> tuple[list[float], list[float]]:
    frame = pd.read_csv(path)
    time = next((c for c in TIME_COLUMNS if c in frame.columns), None)
    pct = next((c for c in PERCENT_COLUMNS if c in frame.columns), None)
    if time is None or pct is None:
        raise SystemExit(f"{path}: need a time column {TIME_COLUMNS} and one of "
                         f"{PERCENT_COLUMNS}; found {list(frame.columns)}")
    return frame[time].tolist(), frame[pct].tolist()


SPEED_COLUMNS = ("Speed_All_Mean", "Avg_Speed", "Speed_Mean")


def _speeds(path: Path) -> tuple[list[float], list[float], str] | None:
    frame = pd.read_csv(path)
    time = next((c for c in TIME_COLUMNS if c in frame.columns), None)
    speed = next((c for c in SPEED_COLUMNS if c in frame.columns), None)
    if time is None or speed is None:
        return None
    return frame[time].tolist(), frame[speed].tolist(), speed


def main() -> int:
    if len(sys.argv) < 4:
        print(__doc__)
        return 2
    stem, rest = sys.argv[1], sys.argv[2:]
    # --reference "label=percentage" draws a horizontal observed benchmark.
    reference = None
    palette = list(COLOURS)
    specs = []
    for item in rest:
        if item.startswith("--colours="):
            palette = [c.strip() for c in item[len("--colours="):].split(",")]
        elif item.startswith("--reference="):
            label, _, value = item[len("--reference="):].partition("=")
            reference = (label, float(value))
        else:
            specs.append(item)

    # Split on "=" first: a label may legitimately contain a comma
    # ("all 2,271 on foot"), and testing the whole spec drew an empty panel.
    with_speed = any("," in spec.partition("=")[2] for spec in specs)
    if with_speed:
        figure, (axis, lower) = plt.subplots(
            2, 1, figsize=(10, 8.6), sharex=True, height_ratios=[1.5, 1],
            gridspec_kw={"hspace": 0.10})
    else:
        figure, axis = plt.subplots(figsize=(10, 6.2))
        lower = None
    notes: list[str] = []

    for i, spec in enumerate(specs):
        label, _, paths = spec.partition("=")
        path, _, speed_path = paths.partition(",")
        minutes, pct = _series(Path(path))
        colour = palette[i % len(palette)]
        axis.plot(minutes, pct, color=colour, linewidth=2.2, label=label)
        final_t, final_p = minutes[-1], pct[-1]
        axis.plot([final_t], [final_p], "o", color=colour, markersize=6)
        if final_p >= 99.95:
            when = next(t for t, p in zip(minutes, pct) if p >= 99.95)
            axis.annotate(f"100% at {when:.0f} min", xy=(when, 100),
                          xytext=(when + max(minutes) * 0.04, 92),
                          color=colour, fontsize=10,
                          arrowprops=dict(arrowstyle="->", color=colour))
            notes.append(f"{label}: complete at {when:.0f} min")
        else:
            axis.annotate(f"{final_p:.1f}% at {final_t:.0f} min",
                          xy=(final_t, final_p),
                          xytext=(final_t * 0.62, final_p - 12),
                          color=colour, fontsize=10,
                          arrowprops=dict(arrowstyle="->", color=colour))
            notes.append(f"{label}: {final_p:.1f}% after {final_t:.0f} min, "
                         "still incomplete")

        if lower is not None and speed_path:
            got = _speeds(Path(speed_path))
            if got:
                s_minutes, s_speed, column = got
                moving = [(m, v) for m, v in zip(s_minutes, s_speed) if v > 0]
                if moving:
                    lower.plot([m for m, _ in moving], [v for _, v in moving],
                               color=colour, linewidth=2.0, label=label)
                    mean = sum(v for _, v in moving) / len(moving)
                    peak = max(v for _, v in moving)
                    notes.append(f"{label}: mean {mean:.2f} m/s of a "
                                 f"{peak:.2f} m/s free flow")

    if lower is None:
        axis.set_xlabel("Minutes since the earthquake")
    axis.set_ylabel("Cumulative evacuated (%)")
    if reference is not None:
        label, value = reference
        axis.axhline(value, color="#111111", linewidth=1.5, linestyle="--",
                     zorder=1)
        axis.annotate(f"{label}: {value:.0f}%", xy=(0, value),
                      xytext=(4, value + 2.5), fontsize=10.5,
                      fontweight="bold", color="#111111")
    axis.set_ylim(0, 103)
    axis.set_xlim(left=0)
    axis.grid(alpha=0.25)
    axis.legend(loc="lower right", fontsize=11, framealpha=0.95)
    axis.set_title("Cumulative evacuation — Arahama", fontsize=14,
                   fontweight="bold", loc="left", pad=12)

    if lower is not None:
        lower.set_xlabel("Minutes since the earthquake")
        lower.set_ylabel("Mean walking speed (m/s)")
        lower.grid(alpha=0.25)
        lower.legend(loc="lower left", fontsize=10, framealpha=0.95)
        lower.set_ylim(bottom=0)

    figure.text(0.008, 0.008, "\n".join(notes), fontsize=9, color="#555555",
                va="bottom")
    # subplots_adjust, not tight_layout: tight_layout silently ignores its rect
    # when a shared-axis grid is present, which left the footnote sitting on top
    # of the x-axis label.
    # Computed in inches, not figure fractions: the same fraction is far less
    # space on a 6.2 inch single-panel figure than on an 8.6 inch two-panel one,
    # which is how the footnote ended up on top of the x-axis label.
    height = figure.get_size_inches()[1]
    reserved = (0.42 + 0.17 * len(notes)) / height
    figure.subplots_adjust(left=0.085, right=0.985, top=0.93,
                           bottom=min(0.32, reserved), hspace=0.10)
    for suffix in ("png", "pdf"):
        figure.savefig(f"{stem}.{suffix}", dpi=200)
    print(f"  {stem}.png / .pdf")
    for note in notes:
        print(f"    {note}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
