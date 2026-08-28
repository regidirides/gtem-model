"""Run many GTEM scenarios from a CSV table and summarise them honestly.

    python batch_main.py --input examples/scenario_list.csv --seed 2026

Each row of the CSV describes one scenario; its ``Count`` column says how many
stochastic replicates to run. Every replicate gets its own seed, drawn from a
master RNG so the whole batch is reproducible from a single ``--seed``.

No single run is presented as a result. The batch always writes
``Aggregated_Summary.csv`` (mean +/- SD +/- n per scenario) alongside the
per-run table, plus a convergence curve showing how many replicates the
estimate actually needed.
"""
from __future__ import annotations

import sys
from pathlib import Path

# Library modules and the simulation engine live in src/.
sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))
import argparse
import os
import time
import traceback
from concurrent.futures import ProcessPoolExecutor, as_completed
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import pynetlogo

import routing
from config import PYTHON_ONLY
from aggregate import (
    aggregate_by_scenario,
    convergence_point,
    write_convergence,
    write_runtime_benchmark,
)
from netlogo_runtime import (
    create_netlogo_link,
    describe_environment,
    detect_netlogo_home,
    jvm_library_path,
)
from validation import (
    ConfigError,
    assert_uniform_dt,
    validate_config,
    validate_zone,
)
from text_strings import TABLES, set_language
from version import VERSION_STAMP

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

REQUIRED_COLUMNS = {
    "Zone", "Adults", "Elderly", "Children", "TR", "Count",
    "Vuln_Low", "Vuln_High", "Tsunami_ETA", "Density_Low", "Density_High",
}

OPTIONAL_DEFAULTS = {
    "End_Of_Simulation": 0.0,
    "DT": 10.0,
    "Road_Width": 2.8,
    "Capacity_Multiplier": 1.0,
    "Max_Snap_Distance": 50.0,
}


@dataclass(frozen=True)
class BatchOptions:
    netlogo_home: str
    memory_mb: int
    reports: bool
    batch_dir: str
    #: Carried explicitly because each replicate runs in its own process, which
    #: imports text_strings fresh and would otherwise default to English.
    language: str = "en"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=f"{VERSION_STAMP} - run GTEM scenarios in batch.")
    parser.add_argument("--input", default="examples/scenario_list.csv",
                        help="CSV table of scenarios.")
    parser.add_argument("--output", default=None,
                        help="Folder name inside Outputs/ (default: timestamp).")
    parser.add_argument("--workers", type=int, default=1,
                        help="Concurrent JVMs. Each uses up to --memory-mb.")
    parser.add_argument("--memory-mb", type=int, default=4096,
                        help="Maximum RAM per JVM.")
    parser.add_argument("--seed", type=int, default=None,
                        help="Master seed. Makes the whole batch reproducible.")
    parser.add_argument("--reports", action="store_true",
                        help="Also write figures and a PDF for every run (slower).")
    parser.add_argument("--language", default="en", choices=sorted(TABLES),
                        help="Language of the figures and the PDF reports. "
                             "Default: en.")
    return parser.parse_args()


def load_experiments(csv_path: Path, master_seed: int | None) -> list[dict[str, Any]]:
    if not csv_path.is_file():
        raise ConfigError(f"Scenario file not found: {csv_path}")

    frame = pd.read_csv(csv_path, sep=None, engine="python")
    frame.columns = frame.columns.str.strip()
    missing = sorted(REQUIRED_COLUMNS - set(frame.columns))
    if missing:
        raise ConfigError(
            f"{csv_path.name} is missing required columns: {', '.join(missing)}")
    if frame.empty:
        raise ConfigError(f"{csv_path.name} contains no rows.")

    for column, default in OPTIONAL_DEFAULTS.items():
        if column not in frame.columns:
            frame[column] = default

    rng = np.random.default_rng(master_seed)
    experiments: list[dict[str, Any]] = []
    run_id = 1
    for row_number, row in frame.iterrows():
        replicates = int(row["Count"])
        if replicates < 1:
            raise ConfigError(
                f"{csv_path.name} row {row_number + 2}: Count must be at least 1.")
        zone = str(row["Zone"]).strip()
        validate_zone(BASE_DIR, zone)
        for _ in range(replicates):
            experiments.append({
                "run_id": run_id,
                "input-zone": zone,
                "total-adults": int(row["Adults"]),
                "total-elderly": int(row["Elderly"]),
                "total-children": int(row["Children"]),
                "departure-mean": float(row["TR"]),
                "tsunami-eta": float(row["Tsunami_ETA"]),
                "end-of-simulation": float(row["End_Of_Simulation"]),
                "dt": float(row["DT"]),
                "average-road-width": float(row["Road_Width"]),
                "road-capacity-multiplier": float(row["Capacity_Multiplier"]),
                "max-snap-distance": float(row["Max_Snap_Distance"]),
                "vulnerability-low": float(row["Vuln_Low"]),
                "vulnerability-high": float(row["Vuln_High"]),
                "density-low": float(row["Density_Low"]),
                "density-high": float(row["Density_High"]),
                "seed": int(rng.integers(1, 2_147_483_647)),
            })
            run_id += 1

    for experiment in experiments:
        validate_config(experiment)
    assert_uniform_dt(experiments)
    return experiments


#: Settings that configure Python rather than the model. Imported, not
#: duplicated - see the note on config.PYTHON_ONLY.
NOT_MODEL_PARAMETERS = PYTHON_ONLY


def run_simulation(experiment: dict[str, Any], options: BatchOptions) -> dict[str, Any]:
    """One replicate, in its own process. Returns a single summary row."""
    os.chdir(BASE_DIR)
    set_language(options.language)
    run_id = int(experiment["run_id"])
    seed = int(experiment["seed"])
    zone = str(experiment["input-zone"])
    output_dir = Path(options.batch_dir) / zone / f"Run_{run_id:04d}_Seed_{seed}"
    output_dir.mkdir(parents=True, exist_ok=True)
    link = None
    started_total = time.perf_counter()

    try:
        link = create_netlogo_link(
            gui=False,
            netlogo_home=options.netlogo_home,
            jvm_path=jvm_library_path(options.netlogo_home),
            jvmargs=[f"-Xmx{options.memory_mb}m", "-Dorg.nlogo.is3d=false"],
        )
        link.load_model(str(MODEL_PATH))
        link.command("set record-video? false")
        # NetLogo resolves relative paths from the model's own folder, so the
        # study-area location is supplied as an absolute path.
        link.command(f'set data-root "{(BASE_DIR / "data").as_posix()}"')

        for key, value in experiment.items():
            if key in NOT_MODEL_PARAMETERS:
                continue
            literal = f'"{value}"' if isinstance(value, str) else str(value)
            link.command(f"set {key} {literal}")

        link.command("set use-fixed-seed? true")
        link.command(f"set input-seed {seed}")

        started_setup = time.perf_counter()
        link.command("setup")
        for key in ("total-adults", "total-elderly", "total-children"):
            link.command(f"set {key} {experiment[key]}")

        routes_path, base_routes_path = routing.resolve_route_tables(zone)
        if routes_path is None:
            raise RuntimeError(f"No route table available for zone '{zone}'.")
        link.command(f'set routes-file "{routes_path.as_posix()}"')
        link.command(f'set base-routes-file '
                     f'"{base_routes_path.as_posix() if base_routes_path else ""}"')

        link.command("load-routes-csv")
        link.command("setup-people")
        seconds_setup = time.perf_counter() - started_setup

        nodes = int(float(link.report("count nodes")))
        links_count = int(float(link.report("count links")))
        agents_created = int(float(link.report("initial-population-simulated")))
        # See main.py: an empty NetLogo list cannot be converted by pyNetLogo.
        warning_count = int(float(link.report("length input-warnings")))

        started_sim = time.perf_counter()
        while str(link.report("run-finished?")).lower() not in ("true", "1", "1.0"):
            link.command("go")
        seconds_sim = time.perf_counter() - started_sim

        evacuated = int(float(link.report("evacuees-safe")))
        caught = int(float(link.report("caught-in-transit")))
        stranded = int(float(link.report("stranded-agents")))
        requested = int(float(link.report("agents-requested")))
        ticks = float(link.report("ticks"))
        dt = float(link.report("dt"))
        not_evacuated = caught + stranded

        result = {
            "Run_ID": run_id,
            "Zone": zone,
            "Seed": seed,
            "GTEM_Version": VERSION_STAMP,
            "Agents_Requested": requested,
            "Agents_Created": agents_created,
            "Evacuated_Before_ETA": evacuated,
            "Not_Evacuated": not_evacuated,
            "Caught_In_Transit": caught,
            "Stranded_No_Route": stranded,
            "Pct_Evacuated": round(evacuated / requested * 100, 3) if requested else 0.0,
            "Pct_Not_Evacuated": round(not_evacuated / requested * 100, 3) if requested else 0.0,
            "Tsunami_ETA_Min": float(experiment["tsunami-eta"]),
            "Elapsed_Min": round(ticks * dt / 60, 3),
            "DT_Seconds": dt,
            "Reaction_Time_Min": float(experiment["departure-mean"]),
            "Nodes": nodes,
            "Links": links_count,
            "Input_Warnings": warning_count,
            "Seconds_Setup": round(seconds_setup, 2),
            "Seconds_Simulation": round(seconds_sim, 2),
            "Seconds_Total": round(time.perf_counter() - started_total, 2),
            "Status": "OK",
            "Error": "",
        }
        pd.DataFrame([result]).to_csv(output_dir / "Run_Summary.csv", index=False)
        return result

    except Exception as exc:
        (output_dir / "FAILED.txt").write_text(traceback.format_exc(), encoding="utf-8")
        return {
            "Run_ID": run_id, "Zone": zone, "Seed": seed,
            "Status": "ERROR",
            "Error": "".join(traceback.format_exception_only(type(exc), exc)).strip(),
            "Seconds_Total": round(time.perf_counter() - started_total, 2),
        }
    finally:
        if link is not None:
            try:
                link.kill_workspace()
            except (AttributeError, pynetlogo.NetLogoException):
                pass


def main() -> int:
    args = parse_args()
    if args.workers < 1 or args.memory_mb < 512:
        raise SystemExit("--workers must be >= 1 and --memory-mb must be >= 512.")

    netlogo_home = detect_netlogo_home()
    if netlogo_home is None:
        raise SystemExit(describe_environment())

    try:
        experiments = load_experiments((BASE_DIR / args.input).resolve(), args.seed)
    except ConfigError as exc:
        print(f"\nConfiguration error:\n{exc}\n")
        return 2

    batch_name = args.output or f"Batch_{datetime.now():%Y%m%d_%H%M%S}"
    batch_dir = BASE_DIR / "Outputs" / batch_name
    batch_dir.mkdir(parents=True, exist_ok=False)
    options = BatchOptions(netlogo_home, args.memory_mb, args.reports,
                           str(batch_dir), args.language)
    # The batch report itself is written in this process, not in a worker.
    set_language(args.language)

    print(f"{VERSION_STAMP} - {len(experiments)} run(s), {args.workers} worker(s)")
    print(f"Master seed: {args.seed if args.seed is not None else 'not set (batch not reproducible)'}")
    print(f"Results: {batch_dir}")

    started = time.monotonic()
    results: list[dict[str, Any]] = []
    with ProcessPoolExecutor(max_workers=args.workers) as executor:
        futures = {executor.submit(run_simulation, e, options): e for e in experiments}
        for future in as_completed(futures):
            result = future.result()
            results.append(result)
            print(f"[{len(results)}/{len(experiments)}] Run {result['Run_ID']}: "
                  f"{result['Status']} ({result['Zone']})")

    runs = pd.DataFrame(results).sort_values("Run_ID")
    # Written before any rendering, so a plotting failure cannot lose results.
    runs.to_csv(batch_dir / "Master_Summary.csv", index=False)

    aggregated = aggregate_by_scenario(runs)
    if not aggregated.empty:
        aggregated.insert(0, "Master_Seed", args.seed if args.seed is not None else "unset")
        aggregated.to_csv(batch_dir / "Aggregated_Summary.csv", index=False)
        print("\nAggregated results (mean +/- SD over n replicates):")
        for _, row in aggregated.iterrows():
            sd = row.get("Pct_Evacuated_SD")
            sd_text = "n/a (1 run)" if pd.isna(sd) else f"{sd:.2f}"
            print(f"  {row['Zone']:<28} evacuated "
                  f"{row['Pct_Evacuated_Mean']:6.2f}% +/- {sd_text}  (n={row['N_Runs']})")

    settled = write_convergence(runs, batch_dir)
    for zone, n_star in settled.items():
        print(f"  {zone:<28} converged at n = "
              f"{n_star if n_star else 'not reached with this many replicates'}")
    write_runtime_benchmark(runs, batch_dir)

    # One report for the whole batch. A single run is not a result, so the
    # batch-level document reports means with their spread.
    if not aggregated.empty:
        import pdf_report
        pdf_report.generate_batch_pdf(str(batch_dir), runs, aggregated,
                                      settled, args.seed)

    elapsed = (time.monotonic() - started) / 60
    errors = int((runs["Status"] != "OK").sum())
    print(f"\nFinished in {elapsed:.2f} min. Successful: {len(runs) - errors}; "
          f"failed: {errors}.")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
