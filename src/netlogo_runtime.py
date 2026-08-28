"""Compatible initialisation of pyNetLogo 0.5.2 with NetLogo 7 and modern Java.

Cross-platform: Windows, macOS and Linux.

Two platform facts drive this module:

1. The JVM shared library has a different name and location on each platform:
       Windows   <NETLOGO_HOME>/runtime/bin/server/jvm.dll
       macOS     <NETLOGO_HOME>/runtime/Contents/Home/lib/server/libjvm.dylib
       Linux     <NETLOGO_HOME>/runtime/lib/server/libjvm.so

2. On macOS and Linux the JVM MUST be started with -Djava.awt.headless=true.
   Without it the model deadlocks permanently, at 0% CPU, with no error, inside
   `gis:fill` during `setup-manzanas`. On macOS this is because Cocoa requires
   AWT on the process main thread while JPype starts the JVM on Python's main
   thread. The failure is silent and indefinite, so it must never be optional.
   Verified on macOS 15 / NetLogo 7.0.4: without the flag setup never returns;
   with it, setup completes in ~2.6 s.
"""

from __future__ import annotations

import os
import platform
from pathlib import Path

import jpype
import pynetlogo
from pynetlogo.core import PYNETLOGO_HOME, find_jars


# Relative paths to the JVM shared library inside a NetLogo installation,
# per platform, in preference order.
_JVM_RELATIVE_PATHS = {
    "Windows": [
        Path("runtime/bin/server/jvm.dll"),
        Path("runtime/bin/client/jvm.dll"),
    ],
    "Darwin": [
        Path("runtime/Contents/Home/lib/server/libjvm.dylib"),
        Path("runtime/Contents/Home/lib/client/libjvm.dylib"),
    ],
    "Linux": [
        Path("runtime/lib/server/libjvm.so"),
        Path("runtime/lib/client/libjvm.so"),
    ],
}

# Default install locations searched when NETLOGO_HOME is not set.
_DEFAULT_INSTALL_DIRS = {
    "Windows": [
        r"C:\Program Files\NetLogo 7.0.4",
        r"C:\Program Files\NetLogo 7.0.2",
        r"C:\Program Files\NetLogo 6.4.0",
    ],
    "Darwin": [
        "/Applications/NetLogo 7.0.4",
        "/Applications/NetLogo 7.0.2",
        "/Applications/NetLogo 6.4.0",
    ],
    "Linux": [
        "/opt/netlogo-7.0.4",
        "/opt/NetLogo 7.0.4",
        str(Path.home() / "NetLogo 7.0.4"),
    ],
}


def jvm_library_path(netlogo_home: str | os.PathLike) -> str | None:
    """Return the JVM shared library inside ``netlogo_home``, or None."""
    root = Path(netlogo_home)
    for relative in _JVM_RELATIVE_PATHS.get(platform.system(), []):
        candidate = root / relative
        if candidate.is_file():
            return str(candidate)
    return None


def detect_netlogo_home() -> str | None:
    """Locate a compatible NetLogo installation, honouring ``NETLOGO_HOME``."""
    candidates = [os.environ.get("NETLOGO_HOME")]
    candidates.extend(_DEFAULT_INSTALL_DIRS.get(platform.system(), []))
    for candidate in candidates:
        if candidate and jvm_library_path(candidate):
            return str(Path(candidate))
    return None


def describe_environment() -> str:
    """Human-readable diagnosis, for error messages aimed at non-experts."""
    system = platform.system()
    home = detect_netlogo_home()
    if home:
        return f"NetLogo found at: {home} (platform: {system})"
    searched = "\n  ".join(_DEFAULT_INSTALL_DIRS.get(system, ["(no known default)"]))
    return (
        f"No NetLogo installation was found on this {system} machine.\n"
        f"Locations searched:\n  {searched}\n"
        "Install NetLogo 7.0.4, or set the NETLOGO_HOME environment variable "
        "to the folder that contains the 'runtime' directory."
    )


def create_netlogo_link(
    *,
    netlogo_home: str,
    jvm_path: str | None = None,
    jvmargs: list[str] | None = None,
    gui: bool = False,
) -> pynetlogo.NetLogoLink:
    """Create the link, avoiding JPype's faulty import hook.

    pyNetLogo imports ``netLogoLink`` as a Java package. With some recent
    Java/JPype versions that import tries to mount the JAR as a filesystem and
    fails. ``JClass`` loads the same class directly and is stable.

    ``jvm_path`` is optional; when omitted it is derived from ``netlogo_home``
    for the current platform.
    """
    if jvm_path is None:
        jvm_path = jvm_library_path(netlogo_home)
    if jvm_path is None:
        raise RuntimeError(describe_environment())

    if not jpype.isJVMStarted():
        jars = find_jars(netlogo_home)
        jars.append(os.path.join(PYNETLOGO_HOME, "java", "netlogolink.jar"))

        args = list(jvmargs or [])
        # Mandatory on macOS/Linux (see module docstring). Harmless on Windows,
        # and only added when the caller has not already specified it.
        if not any(a.startswith("-Djava.awt.headless") for a in args):
            args.append("-Djava.awt.headless=true")

        jpype.startJVM(*args, jvmpath=jvm_path, classpath=jars)

    extensions = Path(netlogo_home) / "extensions"
    if extensions.is_dir():
        jpype.java.lang.System.setProperty("netlogo.extensions.dir", str(extensions))
    if not gui:
        jpype.java.lang.System.setProperty("org.nlogo.preferHeadless", "true")

    wrapper = object.__new__(pynetlogo.NetLogoLink)
    wrapper.netlogo_home = netlogo_home
    wrapper.jvm_home = jvm_path
    java_link = jpype.JClass("netLogoLink.NetLogoLink")
    wrapper.link = java_link(jpype.java.lang.Boolean(gui), jpype.java.lang.Boolean(False))
    return wrapper
