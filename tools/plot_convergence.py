"""Presentation-quality convergence plot from a batch's Master_Summary.csv.

    python tools/plot_convergence.py <Master_Summary.csv> <out_stem> [zone]

Writes <out_stem>.png and <out_stem>.pdf. The convergence point and the
confidence interval come from src/aggregate.py, so the plot cannot disagree with
what GTEM itself reports.
"""
from __future__ import annotations

import math
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import pandas as pd  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from aggregate import (  # noqa: E402
    CV_RELATIVE_TOLERANCE,
    accumulated_cv,
    convergence_point,
    replicates_for_precision,
)

BLUE, GREEN, GREY, RED = "#1565c0", "#2e7d32", "#8a8a8a", "#c62828"


def main() -> int:
    if len(sys.argv) < 3:
        print(__doc__)
        return 2
    source, stem = Path(sys.argv[1]), sys.argv[2]
    zone = sys.argv[3] if len(sys.argv) > 3 else None

    runs = pd.read_csv(source)
    if zone:
        runs = runs[runs["Zone"] == zone]
    values = runs["Pct_Evacuated"].tolist()
    n_runs = len(values)

    curve = accumulated_cv(values)
    ns = [row["N"] for row in curve]
    cvs = [row["CV_Percent"] for row in curve]
    means = [row["Mean"] for row in curve]
    sds = [row["SD"] for row in curve]
    half = [1.96 * sd / math.sqrt(n) for sd, n in zip(sds, ns)]

    n_star = convergence_point(curve)
    final_cv, final_mean = cvs[-1], means[-1]
    needed, achieved = replicates_for_precision(values)

    figure, (top, bottom) = plt.subplots(
        2, 1, figsize=(10, 7.4), sharex=True, height_ratios=[1.05, 1],
        gridspec_kw={"hspace": 0.12})

    # --- accumulated coefficient of variation ------------------------------
    band_lo = final_cv * (1 - CV_RELATIVE_TOLERANCE)
    band_hi = final_cv * (1 + CV_RELATIVE_TOLERANCE)
    top.axhspan(band_lo, band_hi, color=GREEN, alpha=0.11,
                label=f"±{CV_RELATIVE_TOLERANCE:.0%} of the final CV")
    top.axhline(final_cv, color=GREEN, linewidth=1.2, linestyle="--")
    top.plot(ns, cvs, color=BLUE, linewidth=1.9)
    top.set_ylabel("Coefficient of variation (%)")
    top.set_title(
        f"Convergence of the evacuation estimate — {zone or runs['Zone'].iloc[0]}"
        f", {n_runs} replicates",
        fontsize=13, fontweight="bold", loc="left", pad=12)

    if n_star:
        for axis in (top, bottom):
            axis.axvline(n_star, color=RED, linewidth=1.6, linestyle="-.")
        span = max(cvs) - min(cvs)
        top.annotate(
            f"converged at n = {n_star}\nCV stays within "
            f"±{CV_RELATIVE_TOLERANCE:.0%} of {final_cv:.2f}%\nfrom here on",
            xy=(n_star, min(cvs) + span * 0.36),
            xytext=(n_star + n_runs * 0.07, min(cvs) + span * 0.52),
            fontsize=10, color=RED,
            arrowprops=dict(arrowstyle="->", color=RED, linewidth=1.2))
    # Upper LEFT: the curve starts high on the left but drops within a few
    # replicates, and the right-hand side is where the annotation lives.
    top.legend(loc="upper center", fontsize=9, framealpha=0.95)
    top.grid(alpha=0.25)

    # --- running mean with its 95% confidence interval ----------------------
    bottom.fill_between(ns, [m - h for m, h in zip(means, half)],
                        [m + h for m, h in zip(means, half)],
                        color=BLUE, alpha=0.16, label="95% CI of the mean")
    bottom.plot(ns, means, color=BLUE, linewidth=1.9, label="running mean")
    bottom.axhline(final_mean, color=GREY, linewidth=1.1, linestyle=":")
    bottom.set_xlabel("Number of replicates included (accumulated from run 1)")
    bottom.set_ylabel("Evacuated (%)")
    bottom.grid(alpha=0.25)
    bottom.legend(loc="upper right", fontsize=9, framealpha=0.95)

    if n_star:
        idx = n_star - 2  # curve starts at n = 2
        # Anchored to the axis range, not to the CI: the half-width at n=2 is
        # enormous and pushed the label off the bottom of the figure.
        low, high = bottom.get_ylim()
        bottom.annotate(
            f"n = {n_star}:  {means[idx]:.2f}% ± {half[idx]:.2f} pp",
            xy=(n_star, means[idx]),
            xytext=(n_star + n_runs * 0.06, low + (high - low) * 0.14),
            fontsize=10, color=RED,
            arrowprops=dict(arrowstyle="->", color=RED, linewidth=1.2))

    figure.text(
        0.008, 0.012,
        f"Final estimate {final_mean:.2f}% ± {achieved:.2f} pp (95% CI, "
        f"n = {n_runs}).  Reaching ±0.25 pp needs {needed} replicates.  "
        f"Accumulated CV from run 1 — never disjoint bins.",
        fontsize=8.5, color="#555555")

    figure.tight_layout(rect=[0, 0.028, 1, 1])
    for suffix in ("png", "pdf"):
        figure.savefig(f"{stem}.{suffix}", dpi=200)
    print(f"  {stem}.png / .pdf — n*={n_star}, mean {final_mean:.2f}%, "
          f"CV {final_cv:.3f}%")
    return 0


if __name__ == "__main__":
    sys.exit(main())
