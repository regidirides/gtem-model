"""Aggregation and convergence statistics for batches of GTEM runs.

Two concerns:
**no single run may be presented as a result.** Every headline metric is
reported as mean +/- standard deviation over n replicates.
**convergence.** The coefficient of variation is accumulated from run 1
onward (runs 1..2, 1..3, 1..4, ...), never in disjoint bins. Binning hides the
fact that the estimate is still moving; accumulation shows exactly when it
stops moving, which is the only defensible basis for a claim like "40 runs is
enough".
"""

from __future__ import annotations

import math
from pathlib import Path

import pandas as pd

from text_strings import ACTIVE

#: A live view of the selected language, not a snapshot - see text_strings.
T = ACTIVE

#: Metrics aggregated for every scenario.
HEADLINE_METRICS = [
    "Evacuated_Before_ETA",
    "Not_Evacuated",
    "Caught_In_Transit",
    "Stranded_No_Route",
    "Pct_Evacuated",
    "Pct_Not_Evacuated",
    "Elapsed_Min",
]

#: The metric convergence is judged on.
CONVERGENCE_METRIC = "Pct_Evacuated"

#: From the convergence point onward, CV(n) must stay within this FRACTION of
#: its final value. A relative tolerance is essential: an absolute one of, say,
#: 1 percentage point is meaningless when the CV itself is about 1%, and would
#: declare convergence at n = 3 on data that is still clearly moving.
CV_RELATIVE_TOLERANCE = 0.10
#: Minimum number of trailing points required before a claim of convergence.
CV_STABLE_WINDOW = 5
#: Target precision for the MEAN: half-width of its 95% confidence interval,
#: in percentage points. This is the number a planner should actually care
#: about -- "how well do we know the evacuation rate?"
TARGET_CI_HALFWIDTH_PP = 0.25


def aggregate_by_scenario(runs: pd.DataFrame) -> pd.DataFrame:
    """mean, SD and n per scenario for every headline metric."""
    ok = runs.loc[runs.get("Status", "OK") == "OK"].copy()
    if ok.empty:
        return pd.DataFrame()

    rows = []
    for zone, group in ok.groupby("Zone"):
        row: dict[str, object] = {"Zone": zone, "N_Runs": len(group)}
        for metric in HEADLINE_METRICS:
            if metric not in group.columns:
                continue
            values = pd.to_numeric(group[metric], errors="coerce").dropna()
            row[f"{metric}_Mean"] = round(values.mean(), 3) if len(values) else math.nan
            # Sample SD (ddof=1); undefined for a single run, and saying so is
            # more honest than reporting 0.
            row[f"{metric}_SD"] = (round(values.std(ddof=1), 3)
                                   if len(values) > 1 else math.nan)
        rows.append(row)
    return pd.DataFrame(rows).sort_values("Zone").reset_index(drop=True)


def accumulated_cv(values: list[float]) -> list[dict[str, float]]:
    """CV over runs 1..n, for n = 2..len(values). Accumulated, never binned."""
    out: list[dict[str, float]] = []
    for n in range(2, len(values) + 1):
        window = values[:n]
        mean = sum(window) / n
        variance = sum((v - mean) ** 2 for v in window) / (n - 1)
        sd = math.sqrt(variance)
        out.append({
            "N": n,
            "Mean": mean,
            "SD": sd,
            "CV_Percent": (sd / mean * 100) if mean else math.nan,
        })
    return out


def replicates_for_precision(values: list[float],
                             target_pp: float = TARGET_CI_HALFWIDTH_PP) -> tuple[int | None, float]:
    """Smallest n whose 95% CI half-width for the MEAN is below ``target_pp``.

    Uses the SD of the full sample, so this answers "given the variability we
    measured, how many replicates does a future study need?" Returns
    (n, achieved_halfwidth_at_full_sample).
    """
    n_total = len(values)
    if n_total < 2:
        return None, math.nan
    mean = sum(values) / n_total
    sd = math.sqrt(sum((v - mean) ** 2 for v in values) / (n_total - 1))
    achieved = 1.96 * sd / math.sqrt(n_total)
    if sd == 0:
        return 2, 0.0
    needed = math.ceil((1.96 * sd / target_pp) ** 2)
    return needed, achieved


def convergence_point(curve: list[dict[str, float]],
                      relative_tolerance: float = CV_RELATIVE_TOLERANCE,
                      window: int = CV_STABLE_WINDOW) -> int | None:
    """Smallest n from which CV stays within ``tolerance_pp`` of its final value.

    Deliberately NOT "the CV moved less than the tolerance for a few steps in a
    row". Early in the curve, consecutive CV values are close together simply
    because the estimate is barely moving yet -- that test fires almost
    immediately while the estimate is still far from where it ends up. Requiring
    the curve to enter and then REMAIN near its final value is the criterion that
    actually means "more replicates would not change the answer".

    Returns None if the curve never settles, which is the honest answer when the
    batch was too small.
    """
    cvs = [row["CV_Percent"] for row in curve]
    if len(cvs) < window + 1 or any(math.isnan(v) for v in cvs):
        return None
    final = cvs[-1]
    tolerance = abs(final) * relative_tolerance
    if tolerance == 0:
        return int(curve[0]["N"])
    for i in range(len(cvs) - window):
        if all(abs(v - final) <= tolerance for v in cvs[i:]):
            return int(curve[i]["N"])
    return None


def write_convergence(runs: pd.DataFrame, output_dir: Path,
                      metric: str = CONVERGENCE_METRIC) -> dict[str, int | None]:
    """Write Convergence.csv and Figure_Convergence.png; return n* per scenario."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    ok = runs.loc[runs.get("Status", "OK") == "OK"].copy()
    if ok.empty or metric not in ok.columns:
        return {}

    output_dir = Path(output_dir)
    frames: list[pd.DataFrame] = []
    settled: dict[str, int | None] = {}
    precision: dict[str, tuple[int | None, float]] = {}

    figure, axis = plt.subplots(figsize=(10, 6))
    for zone, group in ok.sort_values("Run_ID").groupby("Zone"):
        values = pd.to_numeric(group[metric], errors="coerce").dropna().tolist()
        if len(values) < 3:
            continue
        curve = accumulated_cv(values)
        n_star = convergence_point(curve)
        needed, achieved = replicates_for_precision(values)
        settled[zone] = n_star
        precision[zone] = (needed, achieved)

        frame = pd.DataFrame(curve)
        frame.insert(0, "Zone", zone)
        frame["Metric"] = metric
        # Half-width of the 95% CI of the MEAN at each n: the quantity a
        # planner cares about, expressed in the same units as the metric.
        frame["CI95_HalfWidth"] = [
            1.96 * row["SD"] / math.sqrt(row["N"]) for row in curve]
        frames.append(frame)

        axis.plot([r["N"] for r in curve], [r["CV_Percent"] for r in curve],
                  marker="o", markersize=2.5, linewidth=1.4, label=zone)
        if n_star:
            axis.axvline(n_star, linestyle="--", linewidth=1.0, alpha=0.6)
            axis.annotate(f"n = {n_star}", (n_star, axis.get_ylim()[1] * 0.9),
                          fontsize=9, rotation=90, va="top")

    if not frames:
        plt.close(figure)
        return {}

    pd.concat(frames, ignore_index=True).to_csv(
        output_dir / "Convergence.csv", index=False)

    axis.set_xlabel(T["conv_xlabel"])
    axis.set_ylabel(T["conv_ylabel"].format(metric=metric))
    axis.set_title(T["conv_title"].format(tolerance=CV_RELATIVE_TOLERANCE))
    axis.grid(alpha=0.3)
    axis.legend()
    figure.tight_layout()
    figure.savefig(output_dir / "Figure_Convergence.png", dpi=200)
    plt.close(figure)

    lines = [T["conv_summary_header"].format(metric=CONVERGENCE_METRIC), ""]
    for zone, n_star in settled.items():
        needed, achieved = precision.get(zone, (None, float("nan")))
        lines += [
            f"{zone}:",
            T["conv_settles"].format(n=n_star if n_star else T["conv_not_reached"],
                                     tolerance=CV_RELATIVE_TOLERANCE),
            T["conv_achieved"].format(achieved=achieved),
            T["conv_needed"].format(target=TARGET_CI_HALFWIDTH_PP, needed=needed),
            "",
        ]
    (output_dir / "Convergence_Summary.txt").write_text(
        "\n".join(lines), encoding="utf-8")
    return settled


def write_runtime_benchmark(runs: pd.DataFrame, output_dir: Path) -> None:
    """Runtime against network size, so the speed claim becomes evidence."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    ok = runs.loc[runs.get("Status", "OK") == "OK"].copy()
    needed = {"Nodes", "Links", "Agents_Created", "Seconds_Total"}
    if ok.empty or not needed.issubset(ok.columns):
        return

    output_dir = Path(output_dir)
    figure, (left, right) = plt.subplots(1, 2, figsize=(13, 5))
    for zone, group in ok.groupby("Zone"):
        left.scatter(group["Nodes"], group["Seconds_Total"], s=40, label=zone)
        right.scatter(group["Agents_Created"], group["Seconds_Total"], s=40, label=zone)
    left.set(xlabel=T["bench_xlabel_nodes"], ylabel=T["bench_ylabel"],
             title=T["bench_title_nodes"])
    right.set(xlabel=T["bench_xlabel_agents"], ylabel=T["bench_ylabel"],
              title=T["bench_title_agents"])
    for axis in (left, right):
        axis.grid(alpha=0.3)
        axis.legend()
    figure.tight_layout()
    figure.savefig(output_dir / "Figure_Runtime_Benchmark.png", dpi=200)
    plt.close(figure)
