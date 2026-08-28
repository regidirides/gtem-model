"""Runtime comparison figure: TUNAMI-EVAC1 against GTEM on the same scenario.

    python tools/plot_runtime_comparison.py timings.json out_stem

The input JSON is written by the timing harnesses; see benchmarks/RUNTIME.md.
Two panels: where a single run's time goes, and how a batch scales.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

GREY, BLACK, LIGHT, MID = "#8a8a8a", "#111111", "#cfcfcf", "#5a5a5a"


def main() -> int:
    if len(sys.argv) != 3:
        print(__doc__)
        return 2
    data = json.loads(Path(sys.argv[1]).read_text())
    stem = sys.argv[2]

    single = data["single"]
    batch = data["batch"]

    figure, (left, right) = plt.subplots(1, 2, figsize=(12.5, 5.6))

    # --- single run, split into setup and simulation -----------------------
    labels = [s["label"] for s in single]
    setups = [s["setup_s"] for s in single]
    sims = [s["sim_s"] for s in single]
    colours = [s.get("colour", MID) for s in single]
    x = range(len(labels))
    left.bar(x, setups, color=LIGHT, edgecolor="white", label="setup")
    left.bar(x, sims, bottom=setups, color=colours, edgecolor="white",
             label="simulation")
    for i, (a, b) in enumerate(zip(setups, sims)):
        left.text(i, a + b + max(sims) * 0.02, f"{a + b:.0f} s",
                  ha="center", fontsize=11, fontweight="bold")
    left.set_xticks(list(x))
    left.set_xticklabels(labels, fontsize=9.5)
    left.set_ylabel("Wall-clock seconds")
    left.set_title("One run — Arahama, 2,271 agents", fontsize=12,
                   fontweight="bold", loc="left")
    left.legend(fontsize=9, loc="upper left")
    left.grid(alpha=0.25, axis="y")

    # --- batch -------------------------------------------------------------
    b_labels = [b["label"] for b in batch]
    b_secs = [b["seconds"] for b in batch]
    b_colours = [b.get("colour", MID) for b in batch]
    bx = range(len(b_labels))
    right.bar(bx, b_secs, color=b_colours, edgecolor="white")
    for i, v in enumerate(b_secs):
        right.text(i, v + max(b_secs) * 0.02, f"{v/60:.1f} min",
                   ha="center", fontsize=11, fontweight="bold")
    right.set_xticks(list(bx))
    right.set_xticklabels(b_labels, fontsize=9.5)
    right.set_ylabel("Wall-clock seconds")
    right.set_title(f"A batch of {data['batch_runs']} replicates", fontsize=12,
                    fontweight="bold", loc="left")
    right.grid(alpha=0.25, axis="y")

    figure.suptitle("Runtime — TUNAMI-EVAC1 (2012) against GTEM v1.0.0",
                    fontsize=14, fontweight="bold", x=0.02, ha="left")
    # Wrapped explicitly: a single long line runs off the right edge, which is
    # invisible until the figure is viewed at full width.
    import textwrap
    note = "\n".join(textwrap.wrap(data.get("note", ""), width=132))
    figure.text(0.02, 0.015, note, fontsize=8.5, color="#555555", va="bottom")
    lines = note.count("\n") + 1
    figure.subplots_adjust(left=0.075, right=0.98, top=0.84,
                           bottom=0.16 + 0.028 * lines, wspace=0.22)
    for suffix in ("png", "pdf"):
        figure.savefig(f"{stem}.{suffix}", dpi=200)
    print(f"  {stem}.png / .pdf")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
