"""Run a single GTEM evacuation simulation.

    python main.py --config examples/config_example.txt

Every parameter comes from the configuration file. No Python file needs to be
edited to change a run. A copy of the resolved configuration is written into
the output folder, so a result can always be traced back to its settings.

Exit codes:
    0  the run finished and all outputs were written
    1  the run failed (a FAILED.txt marker is left in the output folder)
    2  the configuration or the input data is invalid (nothing was run)
"""
from __future__ import annotations

import sys
from pathlib import Path

# Library modules and the simulation engine live in src/.
sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))
import argparse
import os
import sys
import traceback
from pathlib import Path
from typing import Any

import pandas as pd
import pynetlogo

import figures
import pdf_report
import routing
from config import PYTHON_ONLY, load_config, write_resolved_copy
from netlogo_runtime import (
    create_netlogo_link,
    describe_environment,
    detect_netlogo_home,
    jvm_library_path,
)
from text_strings import TABLES, set_language
from validation import ConfigError, validate_config, validate_zone
from version import VERSION_STAMP, provenance_line

BASE_DIR = Path(__file__).resolve().parent
def _find_model() -> Path:
    """Locate the engine whether it sits beside this script or in src/.

    Keeping this layout-independent means the entry scripts are identical in a
    flat working copy and in the packaged layout, so copying one to the other
    cannot silently break the model path.
    """
    for candidate in (BASE_DIR / "src" / "gtem_model.nlogox",
                      BASE_DIR / "gtem_model.nlogox"):
        if candidate.is_file():
            return candidate
    return BASE_DIR / "src" / "gtem_model.nlogox"


MODEL_PATH = _find_model()

#: Parameters that exist only in Python and must not be pushed to NetLogo.
#: Imported, not duplicated - see the note on config.PYTHON_ONLY.
NOT_MODEL_PARAMETERS = PYTHON_ONLY

HISTORY_KEYS = (
    "ticks", "evacuated_total", "moving", "speed_mean", "speed_min", "speed_max",
    "evac_adults", "evac_elderly", "evac_children",
    "stranded_agents", "evacuees_safe",
    "speed_adults", "speed_elderly", "speed_children",
)

EXPECTED_OUTPUTS = (
    "Report1_Dynamics.csv", "Report2_Speeds.csv", "Report3_Vulnerability.csv",
    "Report4_SafeZones.csv", "Report5_Congestion.csv",
    "Figure1_Dynamics.png", "Figure2_Speed.png", "Figure3_Vulnerability.png",
    "Figure4_SafeZones.png", "Figure5_Congestion.png",
    "Run_Summary.csv",
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=f"{VERSION_STAMP} - run one evacuation simulation.",
    )
    parser.add_argument(
        "--config", required=True,
        help="Path to the run configuration file (see examples/config_example.txt).",
    )
    parser.add_argument(
        "--output", default=None,
        help="Output folder. Default: Outputs/<zone>/<seed>/",
    )
    parser.add_argument(
        "--language", default=None, choices=sorted(TABLES),
        help="Language of the figures and the PDF report. Overrides the "
             "'language' setting in the configuration file. Default: en.",
    )
    return parser.parse_args()


def collect_state(link: Any, history: dict[str, list[Any]]) -> None:
    sample = {
        "ticks": link.report("last history-time"),
        "evacuated_total": link.report("last history-evacuees"),
        "moving": link.report("last history-moving"),
        "speed_mean": link.report("last history-speed"),
        "speed_min": link.report("last history-speed-min"),
        "speed_max": link.report("last history-speed-max"),
        "evac_adults": link.report("last history-evacuees-adults"),
        "evac_elderly": link.report("last history-evacuees-elderly"),
        "evac_children": link.report("last history-evacuees-children"),
        "stranded_agents": link.report("stranded-agents"),
        "evacuees_safe": link.report("evacuees-safe"),
        "speed_adults": link.report("last history-speed-adults"),
        "speed_elderly": link.report("last history-speed-elderly"),
        "speed_children": link.report("last history-speed-children"),
    }
    for key, value in sample.items():
        history[key].append(value)


def time_margin_pass(link: Any, config: dict[str, Any], seed: int) -> dict[str, Any]:
    """Re-run unbounded to find how much time a full evacuation would need.

    The headline run stops at the tsunami arrival time, so it can say the town
    was short of time but not by how much. This repeats the simulation with the
    same seed and no arrival time, giving identical agent placement and a
    directly comparable curve.

    Costs roughly one extra run, which is why it is opt-in. It must be called
    only after every final value has been read from the model, because it calls
    setup and clears that state.
    """
    link.command("set use-fixed-seed? true")
    link.command(f"set input-seed {seed}")
    link.command("set tsunami-eta 1440")        # 24 h: effectively unbounded
    link.command("set end-of-simulation 0")
    link.command("setup")
    for key in ("total-adults", "total-elderly", "total-children"):
        link.command(f"set {key} {config[key]}")
    link.command("load-routes-csv")
    link.command("setup-people")
    while str(link.report("run-finished?")).lower() not in ("true", "1", "1.0"):
        link.command("go")

    dt = float(link.report("dt"))
    return {
        "minutes": [float(t) * dt / 60 for t in link.report("history-time")],
        "evacuated": [float(e) for e in link.report("history-evacuees")],
        "total_minutes": float(link.report("ticks")) * dt / 60,
        "finally_safe": int(float(link.report("evacuees-safe"))),
        "never_safe": int(float(link.report("stranded-agents"))),
    }


def write_warnings_log(link: Any, output_dir: Path) -> list[str]:
    """Persist the model's input warnings. Silence is recorded explicitly."""
    # pyNetLogo cannot convert an EMPTY NetLogo list: report() raises
    # IndexOutOfBoundsException rather than returning []. Ask for the length
    # first. Without this, a run on clean input data crashes -- the one case
    # nobody would ever hit while testing against flawed data.
    count = int(float(link.report("length input-warnings")))
    warnings = [str(w) for w in link.report("input-warnings")] if count else []
    lines = [f"# Input warnings - {provenance_line()}", ""]
    if warnings:
        lines.append(f"{len(warnings)} warning(s) were raised for this run:")
        lines.append("")
        lines.extend(f"{i}. {w}" for i, w in enumerate(warnings, 1))
    else:
        lines.append("No input warnings.")
    (output_dir / "warnings.log").write_text("\n".join(lines) + "\n", encoding="utf-8")
    return warnings


def run(config: dict[str, Any], output_override: str | None) -> int:
    netlogo_home = detect_netlogo_home()
    if netlogo_home is None:
        print(describe_environment(), file=sys.stderr)
        return 2

    zone = str(config["input-zone"])
    print(f"{VERSION_STAMP} - zone {zone}")

    link = None
    output_dir: Path | None = None
    try:
        link = create_netlogo_link(
            gui=False,
            netlogo_home=netlogo_home,
            jvm_path=jvm_library_path(netlogo_home),
            jvmargs=["-Xmx4096m", "-Dorg.nlogo.is3d=false"],
        )
        link.load_model(str(MODEL_PATH))
        link.command("set record-video? false")
        # NetLogo resolves relative paths from the model's own folder, so the
        # study-area location is supplied as an absolute path.
        link.command(f'set data-root "{(BASE_DIR / "data").as_posix()}"')

        for key, value in config.items():
            if key in NOT_MODEL_PARAMETERS:
                continue
            literal = f'"{value}"' if isinstance(value, str) else str(value)
            link.command(f"set {key} {literal}")

        # A fixed seed must be in place BEFORE setup, because setup draws one.
        requested_seed = int(config.get("seed", 0))
        if requested_seed:
            link.command("set use-fixed-seed? true")
            link.command(f"set input-seed {requested_seed}")
        else:
            link.command("set use-fixed-seed? false")

        print("Running setup...")
        link.command("setup")

        # clear-all wipes these, so re-assert after setup.
        for key in ("total-adults", "total-elderly", "total-children"):
            link.command(f"set {key} {config[key]}")

        seed = int(link.report("current-seed"))
        output_dir = (Path(output_override) if output_override
                      else BASE_DIR / "Outputs" / zone / str(seed))
        output_dir.mkdir(parents=True, exist_ok=True)
        write_resolved_copy(config, output_dir)
        print(f"Seed {seed} - writing to {output_dir}")

        if config.get("recompute_routes"):
            print("Recomputing routes...")
            routing.compute_routes(link, config, force=True)

        # Route tables come from cache/ when available, otherwise the copy
        # shipped in Inputs/. Inputs/ is never written to.
        routes_path, base_routes_path = routing.resolve_route_tables(zone)
        if routes_path is None:
            raise RuntimeError(
                f"No route table for zone '{zone}'.\n"
                "  This zone has never been routed. Add\n"
                "      recompute_routes = true\n"
                "  to the configuration file. It is computed once and cached in "
                "cache/, so later runs are instant."
            )
        link.command(f'set routes-file "{routes_path.as_posix()}"')
        link.command(f'set base-routes-file '
                     f'"{base_routes_path.as_posix() if base_routes_path else ""}"')
        print(f"Route table: {routes_path}")

        link.command("load-routes-csv")
        link.command("setup-people")

        warnings = write_warnings_log(link, output_dir)
        print(f"Input warnings: {len(warnings)}" if warnings else "No input warnings.")

        record_video = bool(config.get("record_video"))
        if record_video:
            link.command("vid:reset-recorder")
            link.command("vid:start-recorder")
            link.command("set record-video? true")

        print("Running simulation...")
        history: dict[str, list[Any]] = {key: [] for key in HISTORY_KEYS}
        if float(link.report("length history-time")) > 0:
            collect_state(link, history)

        # Termination is owned by the model. Polling the agent count instead
        # would spin forever once go() stops internally.
        while str(link.report("run-finished?")).lower() not in ("true", "1", "1.0"):
            link.command("go")
            collect_state(link, history)

        if record_video:
            video_path = output_dir / str(config.get("video_name", "run.mp4"))
            link.command('vid:save-recording "%s"' % str(video_path).replace("\\", "/"))
            print(f"Video: {video_path}")

        evacuated = int(float(link.report("evacuees-safe")))
        caught = int(float(link.report("caught-in-transit")))
        stranded = int(float(link.report("stranded-agents")))
        requested = int(float(link.report("agents-requested")))
        reason = str(link.report("simulation-end-reason"))
        ticks = float(link.report("ticks"))
        dt = float(link.report("dt"))

        not_evacuated = caught + stranded
        print()
        print(f"  Evacuated before the tsunami : {evacuated:6d}  "
              f"({evacuated / requested * 100:5.1f}%)")
        print(f"  NOT evacuated                : {not_evacuated:6d}  "
              f"({not_evacuated / requested * 100:5.1f}%)")
        print(f"      caught in transit        : {caught:6d}")
        print(f"      stranded (no route)      : {stranded:6d}")
        print(f"  Run ended                    : {reason} at "
              f"{ticks * dt / 60:.1f} min")
        print()

        history["vulnerability_records"] = link.report("vulnerability-origin-data")
        history["link_min_speeds"] = link.report("[min-speed-recorded] of links")
        history["shelter_ids"] = link.report("[node-id] of safe-zone-nodes")
        history["shelter_pops"] = link.report("[population] of safe-zone-nodes")
        history["shelter_x"] = link.report("[xcor] of safe-zone-nodes")
        history["shelter_y"] = link.report("[ycor] of safe-zone-nodes")
        history["shelter_names"] = link.report("[node-name] of safe-zone-nodes")
        # Exposure (density integrated over time) first: it is the criticality
        # metric. Peak density is kept alongside it for reference only.
        history["links_congestion"] = link.report(
            "[ (list ([xcor] of end1) ([ycor] of end1) ([xcor] of end2) "
            "([ycor] of end2) density-integral max-density-recorded "
            "congested-seconds ([node-id] of end1) ([node-id] of end2)) ] of links"
        )

        # Only now that every final value has been read is it safe to re-run:
        # the second pass calls setup, which clears the model state above.
        margin = None
        if config.get("time_margin_analysis") and not_evacuated > 0:
            print("Measuring how much more time a full evacuation would need...")
            margin = time_margin_pass(link, config, seed)
            deficit = margin["total_minutes"] - float(config["tsunami-eta"])
            print(f"  a full evacuation needs {margin['total_minutes']:.1f} min; "
                  f"the wave arrives at {float(config['tsunami-eta']):.1f} min "
                  f"({deficit:+.1f} min)")

        if not history["ticks"]:
            raise RuntimeError(
                "The simulation produced no data. Either no agents were created "
                "or they were all resolved before the first tick."
            )

        summary = {
            "GTEM_Version": VERSION_STAMP,
            "Simulation_ID": seed,
            "Zone": zone,
            "Seed": seed,
            "Pop_Adults": config["total-adults"],
            "Pop_Elderly": config["total-elderly"],
            "Pop_Children": config["total-children"],
            "Agents_Requested": requested,
            "Evacuated_Before_ETA": evacuated,
            "Not_Evacuated": not_evacuated,
            "Caught_In_Transit": caught,
            "Stranded_No_Route": stranded,
            "Pct_Evacuated": round(evacuated / requested * 100, 2),
            "Pct_Not_Evacuated": round(not_evacuated / requested * 100, 2),
            "Tsunami_ETA_Min": config["tsunami-eta"],
            "End_Reason": reason,
            "Elapsed_Min": round(ticks * dt / 60, 2),
            "DT_Seconds": dt,
            "Reaction_Time_Min": config["departure-mean"],
            "Road_Width_M": config["average-road-width"],
            "Capacity_Multiplier": config["road-capacity-multiplier"],
            "Input_Warnings": len(warnings),
        }
        if margin:
            summary["Full_Evacuation_Min"] = round(margin["total_minutes"], 2)
            summary["Time_Deficit_Min"] = round(
                margin["total_minutes"] - float(config["tsunami-eta"]), 2)
        pd.DataFrame([summary]).to_csv(output_dir / "Run_Summary.csv", index=False)

        print("Generating figures and report...")
        figures.generate_figures(history, config, str(output_dir))

        missing = [name for name in EXPECTED_OUTPUTS
                   if not (output_dir / name).is_file()]
        if missing:
            raise RuntimeError(f"Expected outputs were not written: {missing}")

        if not pdf_report.generate_pdf_report(str(output_dir), summary, margin):
            raise RuntimeError("The PDF report could not be generated.")

        print(f"Done. Results in {output_dir}")
        link.kill_workspace()
        return 0

    except Exception as exc:
        # Never leave an output folder that looks complete.
        if output_dir is not None:
            try:
                (output_dir / "FAILED.txt").write_text(
                    f"{provenance_line()}\n\nRun failed: "
                    f"{type(exc).__name__}: {exc}\n\n{traceback.format_exc()}",
                    encoding="utf-8",
                )
            except OSError:
                pass
        print(f"\nRUN FAILED: {type(exc).__name__}: {exc}", file=sys.stderr)
        traceback.print_exc()
        if link is not None:
            try:
                link.kill_workspace()
            except (AttributeError, pynetlogo.NetLogoException):
                pass
        return 1


def main() -> int:
    args = parse_args()
    os.chdir(BASE_DIR)
    try:
        config = load_config(args.config)
        # --language wins over the config file, so one configuration can be
        # reported in either language without editing it.
        if args.language:
            config["language"] = args.language
        validate_config(config)
        validate_zone(BASE_DIR, str(config["input-zone"]))
    except ConfigError as exc:
        print(f"\nConfiguration error:\n{exc}\n", file=sys.stderr)
        return 2
    # Selected before anything is drawn; validate_config has already checked it.
    language = set_language(config.get("language", "en"))
    print(f"Report language: {language}")
    return run(config, args.output)


if __name__ == "__main__":
    sys.exit(main())
