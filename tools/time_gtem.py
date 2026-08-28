"""Time GTEM's phases on the same Arahama scenario, matching the TUNAMI harness.

Engine only: no figures, no PDF, and the simulation loop checks completion every
60 model ticks so the measurement is the model's cost, not JPype round-trips.
"""
import json, sys, time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT)); sys.path.insert(0, str(ROOT / "src"))
import os
os.chdir(ROOT)

from config import load_config
from netlogo_runtime import create_netlogo_link, detect_netlogo_home, jvm_library_path
import routing

CONFIG, OUT, REPS = sys.argv[1], sys.argv[2], int(sys.argv[3])
config = load_config(CONFIG)

t0 = time.perf_counter()
home = detect_netlogo_home()
link = create_netlogo_link(gui=False, netlogo_home=home,
                           jvm_path=jvm_library_path(home),
                           jvmargs=["-Xmx4096m", "-Dorg.nlogo.is3d=false"])
link.load_model(str(ROOT / "src" / "gtem_model.nlogox"))
jvm_open = time.perf_counter() - t0

NOT_MODEL = {"seed", "recompute_routes", "record_video", "video_name",
             "time_margin_analysis", "language", "vulnerability-low",
             "vulnerability-high", "density-low", "density-high", "run_id"}
runs = []
for rep in range(REPS):
    seed = 65620156 + rep
    link.command("set record-video? false")
    link.command(f'set data-root "{(ROOT / "data").as_posix()}"')
    for key, value in config.items():
        if key in NOT_MODEL:
            continue
        literal = f'"{value}"' if isinstance(value, str) else str(value)
        link.command(f"set {key} {literal}")
    link.command("set use-fixed-seed? true")
    link.command(f"set input-seed {seed}")

    t1 = time.perf_counter()
    link.command("setup")
    for key in ("total-adults", "total-elderly", "total-children"):
        link.command(f"set {key} {config[key]}")
    routes, base = routing.resolve_route_tables(str(config["input-zone"]))
    link.command(f'set routes-file "{routes.as_posix()}"')
    link.command(f'set base-routes-file "{base.as_posix() if base else ""}"')
    link.command("load-routes-csv")
    link.command("setup-people")
    t_setup = time.perf_counter() - t1

    t2 = time.perf_counter()
    ticks = 0
    while True:
        link.command("repeat 60 [ if not run-finished? [ go ] ]")
        ticks += 60
        if str(link.report("run-finished?")).lower() in ("true", "1", "1.0"):
            break
        if ticks > 6000:
            break
    t_sim = time.perf_counter() - t2
    actual = float(link.report("ticks"))
    runs.append({"seed": seed, "setup_s": t_setup, "sim_s": t_sim,
                 "total_s": t_setup + t_sim, "ticks": actual})
    print(f"  seed {seed}: setup {t_setup:6.1f}s  sim {t_sim:7.1f}s  "
          f"total {t_setup+t_sim:7.1f}s  ticks {actual:.0f}")
    sys.stdout.flush()

json.dump({"jvm_open_s": jvm_open, "runs": runs,
           "agents": int(config["total-adults"]) + int(config["total-elderly"])
                     + int(config["total-children"]),
           "dt": float(config["dt"])}, open(OUT, "w"))
print(f"  JVM+model open: {jvm_open:.1f}s (once per session)")
sys.stdout.flush()
os._exit(0)
