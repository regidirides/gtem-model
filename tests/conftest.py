"""Shared fixtures.

Tests are split in two:

* **Pure tests** need nothing but Python. They run anywhere, including CI.
* **Engine tests** are marked ``@pytest.mark.engine``. They start a JVM and the
  NetLogo model, take roughly a minute each, and are SKIPPED (not failed) when
  NetLogo is not installed, so a contributor without it still gets a useful run.

The JVM is started once per session: JPype cannot restart one in the same
process, and paying the cost per test would make the suite unusable.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))

def _model_path() -> Path:
    """Locate the engine in either the flat or the packaged layout."""
    for candidate in (ROOT / "src" / "gtem_model.nlogox", ROOT / "gtem_model.nlogox"):
        if candidate.is_file():
            return candidate
    return ROOT / "gtem_model.nlogox"

REFERENCE_ZONE = "Chimbote_Zona1"


def pytest_configure(config):
    config.addinivalue_line(
        "markers", "engine: needs NetLogo and a JVM (slow; skipped if absent)")
    config.addinivalue_line(
        "markers", "slow: takes tens of seconds but needs no engine")


def pytest_sessionfinish(session, exitstatus):
    """Remember the real exit status for the hard exit below."""
    session.config._gtem_exit_status = int(exitstatus)


@pytest.hookimpl(trylast=True)
def pytest_unconfigure(config):
    """Exit without letting JPype tear the JVM down.

    WHY THIS EXISTS
        JPype registers an atexit hook that calls DestroyJavaVM, which waits for
        every non-daemon JVM thread to finish. NetLogo leaves one running, so the
        wait never returns: the whole suite would run to completion, print its
        summary, and then hang forever in Threads::destroy_vm(). Observed on
        macOS 15 / NetLogo 7.0.4 - a run sat wedged for over fifteen hours with
        every test already finished, and orphaned processes accumulated across
        sessions.

        Nothing needs saving at this point. Tests are done, the report is
        written, and the JVM is about to be reclaimed by the OS anyway, so
        skipping the orderly teardown costs nothing and buys termination.

    Only fires when a JVM was actually started, so a run without the engine
    tests still exits through the normal path. Set GTEM_CLEAN_JVM_SHUTDOWN=1 to
    disable it and get the old (hanging) behaviour for debugging.
    """
    import os
    import sys

    if os.environ.get("GTEM_CLEAN_JVM_SHUTDOWN"):
        return
    try:
        import jpype
    except ImportError:
        return
    if not jpype.isJVMStarted():
        return

    status = getattr(config, "_gtem_exit_status", 0)
    sys.stdout.flush()
    sys.stderr.flush()
    os._exit(status)


@pytest.fixture(scope="session")
def netlogo_home():
    from netlogo_runtime import detect_netlogo_home
    home = detect_netlogo_home()
    if home is None:
        pytest.skip("NetLogo not installed on this machine")
    return home


@pytest.fixture(scope="session")
def _jvm(netlogo_home):
    """Start the JVM exactly once. JPype cannot restart one in a process."""
    import os

    import jpype
    import pynetlogo
    from pynetlogo.core import PYNETLOGO_HOME, find_jars

    from netlogo_runtime import jvm_library_path

    os.chdir(ROOT)
    if not jpype.isJVMStarted():
        jars = find_jars(netlogo_home)
        jars.append(os.path.join(PYNETLOGO_HOME, "java", "netlogolink.jar"))
        jpype.startJVM(
            "-Xmx4096m", "-Dorg.nlogo.is3d=false",
            "-Djava.awt.headless=true",   # mandatory on macOS/Linux
            jvmpath=jvm_library_path(netlogo_home), classpath=jars)
        jpype.java.lang.System.setProperty(
            "netlogo.extensions.dir", os.path.join(netlogo_home, "extensions"))
        jpype.java.lang.System.setProperty("org.nlogo.preferHeadless", "true")

    class Run:
        """One configured, completed (or setup-only) model run."""

        def __init__(self, **overrides):
            import routing

            self.link = object.__new__(pynetlogo.NetLogoLink)
            self.link.netlogo_home = netlogo_home
            self.link.jvm_home = ""
            self.link.link = jpype.JClass("netLogoLink.NetLogoLink")(
                jpype.java.lang.Boolean(False), jpype.java.lang.Boolean(False))
            self.link.load_model(str(_model_path()))

            settings = {
                "input-zone": f'"{overrides.pop("zone", REFERENCE_ZONE)}"',
                "dt": 10, "departure-mean": 5, "tsunami-eta": 23,
                "end-of-simulation": 0, "average-road-width": 2.8,
                "road-capacity-multiplier": 1, "max-snap-distance": 50,
                "use-fixed-seed?": "true", "input-seed": 12345,
                "record-video?": "false",
            }
            self.people = {"total-adults": overrides.pop("adults", 200),
                           "total-elderly": overrides.pop("elderly", 40),
                           "total-children": overrides.pop("children", 60)}
            settings.update(overrides)
            for key, value in settings.items():
                self.link.command(f"set {key} {value}")
            self.link.command("setup")
            for key, value in self.people.items():
                self.link.command(f"set {key} {value}")

            zone = str(self.report("input-zone"))
            routes, base = routing.resolve_route_tables(zone)
            if routes is None:
                # A freshly generated fixture zone has never been routed.
                routing.compute_routes(self.link, {"input-zone": zone})
                routes, base = routing.resolve_route_tables(zone)
            self.link.command(f'set routes-file "{routes.as_posix()}"')
            self.link.command(
                f'set base-routes-file "{base.as_posix() if base else ""}"')

        def report(self, expression):
            return self.link.report(expression)

        def number(self, expression):
            return float(self.link.report(expression))

        def populate(self):
            self.link.command("load-routes-csv")
            self.link.command("setup-people")
            return self

        def run_to_end(self):
            while str(self.report("run-finished?")).lower() not in ("true", "1", "1.0"):
                self.link.command("go")
            return self

        def close(self):
            try:
                self.link.kill_workspace()
            except Exception:  # noqa: BLE001 - teardown must not mask a failure
                pass

    return Run


@pytest.fixture
def engine(_jvm):
    """Factory for model runs, closed at the END OF EACH TEST.

    Deliberately function-scoped. An earlier version was session-scoped and only
    closed workspaces at session teardown; by the end of a full run that left
    ~35 NetLogoLink workspaces open in one JVM, and tests that passed in
    isolation began failing. The JVM is still started once, via _jvm.
    """
    created: list = []

    def factory(**overrides):
        run = _jvm(**overrides)
        created.append(run)
        return run

    yield factory

    for run in created:
        run.close()
