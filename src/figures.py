"""Figures and CSV reports for one GTEM run.

Five figures, each answering a question a planner actually asks.

Every figure obeys three rules:
  1. People who did NOT evacuate are always visible. A blank area must mean
     "nobody started here", never "everybody here died".
  2. Colour ranges are fixed by the configured thresholds, so two scenarios can
     be compared side by side.
  3. Nothing is labelled by a bare internal ID where a name is available.
"""

from __future__ import annotations

import matplotlib

matplotlib.use("Agg")  # no display, and safe under multiprocessing

import matplotlib.colors as mcolors
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from text_strings import (
    ACTIVE,
    OUTCOME_CAUGHT,
    OUTCOME_EVACUATED,
    OUTCOME_STRANDED,
)
from version import VERSION_STAMP

#: A live view of the selected language, not a snapshot - see text_strings.
T = ACTIVE

GREEN, AMBER, RED, BLACK = "#2e7d32", "#f9a825", "#c62828", "#111111"
GREY = "#cfcfcf"
TOP_SAFE_ZONES = 5
TOP_CONGESTED = 10


def _stamp(figure) -> None:
    """Every figure carries the version that produced it."""
    figure.text(0.995, 0.005, VERSION_STAMP, ha="right", va="bottom",
                fontsize=6, color="#888888")


def _save(figure, path: str) -> None:
    _stamp(figure)
    figure.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(figure)


def _series(data: dict, key: str, length: int) -> np.ndarray:
    values = data.get(key)
    if values is None or len(values) == 0:
        return np.zeros(length, dtype=float)
    array = np.asarray(values, dtype=float)
    if len(array) != length:
        raise ValueError(
            f"Series '{key}' has {len(array)} points; expected {length}. "
            "The model and the reporting layer are out of step."
        )
    return array


# ---------------------------------------------------------------- figure 1
def _figure_dynamics(data, config, out, minutes, totals):
    groups = [
        ("adults", T["adults"], "evac_adults", totals["adults"]),
        ("elderly", T["elderly"], "evac_elderly", totals["elderly"]),
        ("children", T["children"], "evac_children", totals["children"]),
    ]
    eta = float(config.get("tsunami-eta", 0) or 0)

    figure, axes = plt.subplots(3, 1, figsize=(10, 11), sharex=True)
    figure.suptitle(f"{T['fig1_title']}\n{T['fig1_suptitle']}", fontsize=13)

    for axis, (_key, label, series_key, total) in zip(axes, groups):
        evacuated = _series(data, series_key, len(minutes))
        pct = (evacuated / total * 100) if total > 0 else np.zeros_like(evacuated)
        axis.plot(minutes, pct, linewidth=2.0, color="#1565c0", label=label)
        axis.fill_between(minutes, 0, pct, alpha=0.15, color="#1565c0")
        if eta > 0:
            axis.axvline(eta, color=RED, linewidth=1.8)
            axis.axvspan(eta, max(minutes.max(), eta), color=RED, alpha=0.06)
        axis.set_ylim(0, 100)
        axis.set_ylabel(T["fig1_ylabel"])
        final = pct[-1] if len(pct) else 0.0
        axis.set_title(T["fig1_panel"].format(
            group=label, pct=final,
            evacuated=int(evacuated[-1]) if len(evacuated) else 0,
            total=int(total)), fontsize=11, loc="left")
        axis.grid(alpha=0.3)

    if eta > 0:
        axes[0].legend([plt.Line2D([], [], color=RED, linewidth=1.8)],
                       [T["fig1_eta_label"].format(eta=eta)], loc="lower right")
    axes[-1].set_xlabel(T["fig1_xlabel"])
    _save(figure, f"{out}/Figure1_Dynamics.png")


# ---------------------------------------------------------------- figure 2
def _figure_speed(data, out, minutes):
    figure, axes = plt.subplots(3, 1, figsize=(10, 11), sharex=True, sharey=True)
    figure.suptitle(f"{T['fig2_title']}\n{T['fig2_suptitle']}", fontsize=13)

    free_flow = {
        T["adults"]: float(np.nanmax(_series(data, "speed_adults", len(minutes)))
                           or 0) or 1.33,
    }
    for axis, (label, key) in zip(axes, [
        (T["adults"], "speed_adults"),
        (T["elderly"], "speed_elderly"),
        (T["children"], "speed_children"),
    ]):
        speeds = _series(data, key, len(minutes))
        moving = speeds > 0
        axis.plot(minutes[moving], speeds[moving], linewidth=1.8, color="#1565c0")
        if moving.any():
            reference = float(np.nanmax(speeds))
            axis.axhline(reference, color="#888888", linestyle=":", linewidth=1.2,
                         label=T["fig2_free_flow"].format(v=reference))
            axis.legend(loc="lower left", fontsize=9)
        axis.set_ylabel(T["speed_ms"])
        axis.set_title(label, fontsize=11, loc="left")
        axis.grid(alpha=0.3)

    axes[-1].set_xlabel(T["fig1_xlabel"])
    _save(figure, f"{out}/Figure2_Speed.png")
    _ = free_flow


# ---------------------------------------------------------------- figure 3
def _figure_vulnerability(data, config, out, dt):
    records = np.asarray(data.get("vulnerability_records", []), dtype=float)
    low = float(config.get("vulnerability-low", 11))
    high = float(config.get("vulnerability-high", 17))

    if records.size == 0:
        figure = plt.figure(figsize=(10, 9))
        plt.text(0.5, 0.5, T["fig3_no_data"], ha="center", va="center")
        plt.axis("off")
        pd.DataFrame(columns=["X", "Y", T["col_minutes"], T["col_outcome"]]).to_csv(
            f"{out}/Report3_Vulnerability.csv", index=False)
        _save(figure, f"{out}/Figure3_Vulnerability.png")
        return

    x, y = records[:, 0], records[:, 1]
    minutes = records[:, 2] * dt / 60.0
    # The fourth column is the terminal outcome, so non-evacuees are plotted too.
    outcome = (records[:, 3].astype(int) if records.shape[1] > 3
               else np.full(len(records), OUTCOME_EVACUATED))

    names = {OUTCOME_EVACUATED: "evacuated",
             OUTCOME_CAUGHT: "caught_in_transit",
             OUTCOME_STRANDED: "stranded_no_route"}
    pd.DataFrame({
        "X": x, "Y": y,
        T["col_minutes"]: np.where(outcome == OUTCOME_EVACUATED, minutes, np.nan),
        T["col_outcome"]: [names.get(int(o), "unknown") for o in outcome],
    }).to_csv(f"{out}/Report3_Vulnerability.csv", index=False)

    evacuated = outcome == OUTCOME_EVACUATED
    failed = ~evacuated

    figure, axis = plt.subplots(figsize=(11, 9))
    # Draw fastest first so the slow and the failed stay visible on top.
    for mask, colour, label in (
        (evacuated & (minutes < low), GREEN,
         T["fig3_legend_fast"].format(low=low)),
        (evacuated & (minutes >= low) & (minutes <= high), AMBER,
         T["fig3_legend_mid"].format(low=low, high=high)),
        (evacuated & (minutes > high), RED,
         T["fig3_legend_slow"].format(high=high)),
        (failed, BLACK, T["fig3_legend_failed"]),
    ):
        if mask.any():
            axis.scatter(x[mask], y[mask], s=14, c=colour, edgecolors="none",
                         alpha=0.85, label=f"{label}  (n={int(mask.sum())})")

    axis.set_aspect("equal")
    axis.set_title(f"{T['fig3_title']}\n{T['fig3_subtitle']}", fontsize=12)
    axis.legend(loc="upper right", fontsize=9, framealpha=0.92)
    axis.grid(alpha=0.2)
    _save(figure, f"{out}/Figure3_Vulnerability.png")


# ---------------------------------------------------------------- figure 4
def _figure_safe_zones(data, out):
    ids = np.asarray(data.get("shelter_ids", []), dtype=float)
    received = np.asarray(data.get("shelter_pops", []), dtype=float)
    # Use the coordinates the model reports directly. Reconstructing them by
    # scanning link endpoints would silently drop any safe zone with no link.
    xs = np.asarray(data.get("shelter_x", []), dtype=float)
    ys = np.asarray(data.get("shelter_y", []), dtype=float)
    raw_names = data.get("shelter_names") or []
    names = [str(n) if str(n).strip() not in ("", "0", "nobody")
             else f"{T['safe_zone'].title()} {int(i)}"
             for n, i in zip(list(raw_names) + [""] * len(ids), ids)]

    order = np.argsort(-received) if received.size else np.array([], dtype=int)
    pd.DataFrame({
        "Rank": np.arange(1, len(order) + 1),
        "Safe_Zone_ID": ids[order].astype(int) if len(order) else [],
        "Name": [names[i] for i in order],
        "People_Received": received[order].astype(int) if len(order) else [],
    }).to_csv(f"{out}/Report4_SafeZones.csv", index=False)

    figure, axis = plt.subplots(figsize=(11, 9))
    if len(order) == 0 or xs.size != ids.size:
        axis.text(0.5, 0.5, T["fig4_unused"], ha="center", va="center")
        axis.axis("off")
        _save(figure, f"{out}/Figure4_SafeZones.png")
        return

    used = received > 0
    if (~used).any():
        axis.scatter(xs[~used], ys[~used], marker="*", s=160, c=GREY,
                     edgecolors="black", linewidths=0.8, label=T["fig4_unused"])
    if used.any():
        sizes = 180 + 900 * (received[used] / received[used].max())
        points = axis.scatter(xs[used], ys[used], marker="*", s=sizes,
                              c=received[used], cmap="YlOrRd",
                              edgecolors="black", linewidths=0.9, zorder=5)
        figure.colorbar(points, ax=axis, label=T["fig4_people_received"],
                        fraction=0.035)

    # Label only zones that actually received people: a "0" label adds nothing
    # and crowds the others. Offsets alternate around the marker so that two
    # nearby zones do not overprint each other.
    labelled = [i for i in order[:TOP_SAFE_ZONES] if received[i] > 0]
    # Breathing room first, so the axis limits used below are the final ones.
    axis.margins(0.20)
    x_mid = sum(axis.get_xlim()) / 2
    y_mid = sum(axis.get_ylim()) / 2
    # Distinct vertical offset per rank: two safe zones only a few metres apart
    # would otherwise have their labels land on top of one another.
    spacing = [16, 30, 46, 62, 78]
    for rank, index in enumerate(labelled, start=1):
        # Push each label towards the middle of the plot so one near an edge
        # cannot be clipped.
        dx = 18 if xs[index] < x_mid else -18
        dy = spacing[(rank - 1) % len(spacing)] * (1 if ys[index] < y_mid else -1)
        axis.annotate(f"{rank}. {names[index]}\n{int(received[index]):,}",
                      (xs[index], ys[index]), textcoords="offset points",
                      xytext=(dx, dy), fontsize=8,
                      ha="left" if dx > 0 else "right", fontweight="bold",
                      bbox=dict(boxstyle="round,pad=0.25", fc="white",
                                ec="#555555", alpha=0.92),
                      arrowprops=dict(arrowstyle="-", color="#777777", lw=0.6))

    axis.set_aspect("equal")
    axis.set_title(f"{T['fig4_title']}\n"
                   f"{T['fig4_subtitle'].format(n=len(labelled))}",
                   fontsize=12)
    # Only when something carries a label: when every safe zone received someone
    # there is no "received nobody" marker, and matplotlib warns on an empty
    # legend. The warning surfaced on a clean Arahama run.
    if axis.get_legend_handles_labels()[0]:
        axis.legend(loc="lower right", fontsize=9)
    axis.grid(alpha=0.2)
    _save(figure, f"{out}/Figure4_SafeZones.png")


# ---------------------------------------------------------------- figure 5
def _figure_congestion(data, out):
    links = np.asarray(data.get("links_congestion", []), dtype=float)
    if links.size == 0:
        figure = plt.figure(figsize=(11, 9))
        plt.text(0.5, 0.5, T["fig5_no_data"], ha="center", va="center")
        plt.axis("off")
        pd.DataFrame(columns=["x1", "y1", "x2", "y2", "Exposure", "Peak_Density",
                              "Congested_Seconds", "start_node", "end_node"]
                     ).to_csv(f"{out}/Report5_Congestion.csv", index=False)
        _save(figure, f"{out}/Figure5_Congestion.png")
        return

    x1, y1, x2, y2 = links[:, 0], links[:, 1], links[:, 2], links[:, 3]
    exposure, peak, seconds = links[:, 4], links[:, 5], links[:, 6]
    node_a, node_b = links[:, 7], links[:, 8]

    order = np.argsort(-exposure)
    pd.DataFrame({
        "Rank": np.arange(1, len(order) + 1),
        "start_node": node_a[order].astype(int),
        "end_node": node_b[order].astype(int),
        "Exposure": exposure[order],
        "Peak_Density": peak[order],
        "Congested_Seconds": seconds[order],
        "x1": x1[order], "y1": y1[order], "x2": x2[order], "y2": y2[order],
    }).to_csv(f"{out}/Report5_Congestion.csv", index=False)

    import matplotlib.collections as mc

    figure, axis = plt.subplots(figsize=(12, 10))
    segments = [[(a, b), (c, d)] for a, b, c, d in zip(x1, y1, x2, y2)]
    used = exposure > 0

    idle = [segments[i] for i in range(len(segments)) if not used[i]]
    if idle:
        axis.add_collection(mc.LineCollection(idle, colors=GREY, linewidths=0.8,
                                              zorder=1))
    if used.any():
        busy = [segments[i] for i in range(len(segments)) if used[i]]
        values = exposure[used]
        collection = mc.LineCollection(
            busy, cmap="YlOrRd",
            norm=mcolors.Normalize(vmin=0, vmax=float(values.max())),
            linewidths=2.4, zorder=3)
        collection.set_array(values)
        axis.add_collection(collection)
        figure.colorbar(collection, ax=axis, label=T["fig5_colorbar"],
                        fraction=0.035)

    ranking = [T["fig5_ranking"]]
    for rank, index in enumerate(order[:TOP_CONGESTED], start=1):
        if exposure[index] <= 0:
            break
        axis.text((x1[index] + x2[index]) / 2, (y1[index] + y2[index]) / 2,
                  str(rank), fontsize=6, fontweight="bold", ha="center",
                  va="center", zorder=8,
                  bbox=dict(boxstyle="circle,pad=0.16", fc="white", ec=RED,
                            alpha=0.95))
        ranking.append(T["fig5_rank_row"].format(
            rank=rank, a=int(node_a[index]), b=int(node_b[index]),
            value=exposure[index]))

    axis.text(0.02, 0.98, "\n".join(ranking), transform=axis.transAxes,
              fontsize=8.5, va="top", fontweight="bold",
              bbox=dict(boxstyle="round", fc="white", ec="#777777", alpha=0.9))
    axis.autoscale()
    axis.set_aspect("equal")
    axis.set_title(f"{T['fig5_title']}\n{T['fig5_subtitle']}", fontsize=12)
    _save(figure, f"{out}/Figure5_Congestion.png")


# ---------------------------------------------------------------- entry point
def generate_figures(data: dict, config: dict, output_folder: str) -> None:
    """Write every CSV report and figure for one run."""
    import os

    os.makedirs(output_folder, exist_ok=True)
    dt = float(config["dt"])
    ticks = np.asarray(data["ticks"], dtype=float)
    minutes = ticks * dt / 60.0
    length = len(ticks)

    totals = {
        "adults": float(config.get("total-adults", 0)),
        "elderly": float(config.get("total-elderly", 0)),
        "children": float(config.get("total-children", 0)),
    }
    population = sum(totals.values())

    evacuated = _series(data, "evacuees_safe", length)
    moving = _series(data, "moving", length)
    stranded = _series(data, "stranded_agents", length)
    not_evacuated = moving + stranded

    pd.DataFrame({
        "Ticks": ticks,
        T["col_minutes"]: minutes,
        "Evacuated": evacuated,
        "Not_Evacuated": not_evacuated,
        "Still_Moving": moving,
        "Stranded": stranded,
        "Pct_Evacuated": evacuated / population * 100 if population else 0,
        "Pct_Not_Evacuated": not_evacuated / population * 100 if population else 0,
        "Evac_Adults": _series(data, "evac_adults", length),
        "Evac_Elderly": _series(data, "evac_elderly", length),
        "Evac_Children": _series(data, "evac_children", length),
    }).to_csv(f"{output_folder}/Report1_Dynamics.csv", index=False)

    pd.DataFrame({
        "Ticks": ticks,
        T["col_minutes"]: minutes,
        "Speed_Adults": _series(data, "speed_adults", length),
        "Speed_Elderly": _series(data, "speed_elderly", length),
        "Speed_Children": _series(data, "speed_children", length),
        "Speed_All_Mean": _series(data, "speed_mean", length),
    }).to_csv(f"{output_folder}/Report2_Speeds.csv", index=False)

    _figure_dynamics(data, config, output_folder, minutes, totals)
    _figure_speed(data, output_folder, minutes)
    _figure_vulnerability(data, config, output_folder, dt)
    _figure_safe_zones(data, output_folder)
    _figure_congestion(data, output_folder)
