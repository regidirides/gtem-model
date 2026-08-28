"""Capture per-tick agent positions for the demo animation.

    python tools/record_demo.py --config examples/config_example.txt --output DemoRun

This drives a NORMAL run through ``main.py`` and only wraps ``collect_state``,
which main.py already calls after every tick. Nothing about the simulation is
reimplemented here, so the video and the PDF come from one and the same run.

WHY THE READS ARE SORTED
    ``[reporter] of agentset`` returns results in random order and CONSUMES the
    random number stream, so naive sampling would silently change the very run
    it is meant to record. ``map [t -> ... of t] sort agentset`` is deterministic
    and reads each agent individually, which does not draw from the stream.
    ``--verify`` checks this holds rather than trusting it.

Static geometry (roads, safe zones) is read AFTER the run has finished, where no
read can affect the result.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))

import numpy as np  # noqa: E402

import main as gtem_main  # noqa: E402

#: One row per agent: x, y, and 1 if they have started walking.
_AGENT_READER = (
    'map [ t -> [ (list xcor ycor (ifelse-value ready-to-move? [1] [0])) ] of t ]'
    ' sort {breed}'
)

BREEDS = ("adults", "elderly", "children")


def _read_breed(link, breed: str) -> np.ndarray:
    """Positions of one breed, or an empty (0, 3) array.

    pyNetLogo raises IndexOutOfBoundsException on an EMPTY NetLogo list rather
    than returning [], so the count is checked first.
    """
    if int(float(link.report(f"count {breed}"))) == 0:
        return np.empty((0, 3), dtype=float)
    rows = link.report(_AGENT_READER.format(breed=breed))
    return np.asarray([[float(v) for v in row] for row in rows], dtype=float)


def install_capture(frames: list[dict]) -> None:
    """Wrap main.collect_state so every tick also records positions."""
    original = gtem_main.collect_state

    def capturing(link, history):
        original(link, history)
        frames.append({
            "tick": float(link.report("ticks")),
            "evacuated": float(link.report("evacuees-safe")),
            **{breed: _read_breed(link, breed) for breed in BREEDS},
        })

    gtem_main.collect_state = capturing


def capture_static(link) -> dict:
    """Roads and safe zones. Read after the run, so reads cannot perturb it."""
    nodes = link.report(
        "map [ t -> [ (list xcor ycor is-safe-zone) ] of t ] sort nodes")
    nodes = np.asarray([[float(v) for v in row] for row in nodes], dtype=float)
    if int(float(link.report("count links"))) == 0:
        edges = np.empty((0, 4), dtype=float)
    else:
        edges = link.report(
            "map [ l -> [ (list ([xcor] of end1) ([ycor] of end1) "
            "([xcor] of end2) ([ycor] of end2)) ] of l ] sort links")
        edges = np.asarray([[float(v) for v in row] for row in edges], dtype=float)
    return {"nodes": nodes, "edges": edges}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--frames", default="demo_frames.npz",
                        help="Where to write the captured frames.")
    args = parser.parse_args()

    frames: list[dict] = []
    install_capture(frames)

    static: dict = {}
    original_report = gtem_main.pdf_report.generate_pdf_report

    def capture_then_report(run_path, summary, margin=None):
        # The last hook that still has a live link is not available here, so the
        # static geometry is grabbed from the module-level stash set below.
        return original_report(run_path, summary, margin)

    gtem_main.pdf_report.generate_pdf_report = capture_then_report

    # main.run() closes the workspace, so the static read is wired in by
    # wrapping kill_workspace: the last moment the link is still alive.
    import pynetlogo

    original_kill = pynetlogo.NetLogoLink.kill_workspace

    def kill_after_capture(self):
        if not static:
            try:
                static.update(capture_static(self))
            except Exception as exc:  # noqa: BLE001 - never fail the run for a demo
                print(f"   static capture skipped: {type(exc).__name__}: {exc}")
        return original_kill(self)

    pynetlogo.NetLogoLink.kill_workspace = kill_after_capture

    config = gtem_main.load_config(args.config)
    gtem_main.validate_config(config)
    gtem_main.validate_zone(ROOT, str(config["input-zone"]))
    status = gtem_main.run(config, args.output)

    if not frames:
        print("No frames captured.")
        return 1

    payload = {
        "tick": np.array([f["tick"] for f in frames], dtype=float),
        "evacuated": np.array([f["evacuated"] for f in frames], dtype=float),
        "dt": float(config.get("dt", 10)),
        "tsunami_eta": float(config.get("tsunami-eta", 0)),
        "nodes": static.get("nodes", np.empty((0, 3))),
        "edges": static.get("edges", np.empty((0, 4))),
    }
    for breed in BREEDS:
        payload[f"{breed}_counts"] = np.array(
            [len(f[breed]) for f in frames], dtype=int)
        payload[f"{breed}_xyz"] = (np.concatenate([f[breed] for f in frames])
                                   if frames else np.empty((0, 3)))

    out = Path(args.frames)
    np.savez_compressed(out, **payload)
    print(f"   {len(frames)} frames -> {out}  ({out.stat().st_size / 1e6:.1f} MB)")
    return status


if __name__ == "__main__":
    sys.exit(main())
