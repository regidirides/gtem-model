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


#: Mach-O CPU types we care about on macOS.
_CPU_TYPES = {0x01000007: "x86_64", 0x0100000C: "arm64",
              0x00000007: "i386", 0x0000000C: "arm"}


def library_architectures(path: str | os.PathLike) -> list[str]:
    """Architectures inside a Mach-O library, read from its header.

    Used to explain a JVM that exists but will not load. Returns [] on any
    other platform or on an unrecognised file, so callers must treat an empty
    list as "unknown", never as "incompatible".
    """
    try:
        with open(path, "rb") as handle:
            head = handle.read(4096)
    except OSError:
        return []
    if len(head) < 8:
        return []
    magic = head[:4]
    if magic in (b"\xcf\xfa\xed\xfe", b"\xce\xfa\xed\xfe"):   # thin
        return [_CPU_TYPES.get(int.from_bytes(head[4:8], "little"), "unknown")]
    if magic in (b"\xca\xfe\xba\xbe", b"\xca\xfe\xba\xbf"):   # universal
        width = 20 if magic.endswith(b"\xbe") else 32
        count = min(int.from_bytes(head[4:8], "big"), 16)
        found = []
        for i in range(count):
            start = 8 + i * width
            if start + 4 > len(head):
                break
            found.append(_CPU_TYPES.get(
                int.from_bytes(head[start:start + 4], "big"), "unknown"))
        return found
    return []


def diagnose_jvm_failure(jvm_path: str, error: BaseException) -> str:
    """Explain why a JVM that exists on disk could not be loaded.

    JPype reports a failed dlopen as "JVM DLL not found", which sends people
    looking for a missing file when the file is plainly there. On macOS the
    usual cause is an architecture mismatch: an Intel Python cannot load an
    Apple-Silicon JVM, or the reverse.
    """
    lines = [f"NetLogo's Java runtime could not be loaded:", f"  {jvm_path}"]
    if not Path(jvm_path).is_file():
        lines.append("")
        lines.append("The file is missing. Reinstall NetLogo, or point "
                     "NETLOGO_HOME at the right folder.")
        return "\n".join(lines)

    lines.append("")
    lines.append("The file exists, so this is a load failure, not a missing file.")
    host = platform.machine()
    have = library_architectures(jvm_path)
    if have:
        lines.append(f"  Python is running as : {host}")
        lines.append(f"  That Java runtime is : {', '.join(have)}")
    if have and host not in have:
        lines.append("")
        lines.append("THESE DO NOT MATCH, which is almost certainly the problem.")
        lines.append("A Python interpreter cannot load a library built for a "
                     "different processor.")
        lines.append("")
        if host == "x86_64" and "arm64" in have:
            lines.append("You are on an Intel build of Python on an Apple Silicon "
                         "Mac. Anaconda installed at /opt/anaconda3 is commonly "
                         "the Intel build, and it runs under Rosetta.")
            lines.append("")
            lines.append("Fix: recreate the environment with a native arm64 "
                         "Python. Miniforge is the simplest route:")
            lines.append("  https://github.com/conda-forge/miniforge")
            lines.append("  conda env create -f environment.yml")
            lines.append("  conda activate gtem")
            lines.append("")
            lines.append("Check afterwards with:")
            lines.append('  python -c "import platform; print(platform.machine())"')
            lines.append("It must print arm64.")
        else:
            lines.append("Install a Python whose architecture matches the Java "
                         "runtime, or a NetLogo build that matches your Python.")
    elif not have:
        lines.append("")
        lines.append("The architecture could not be read from the file, so the "
                     "cause is unclear. It may be quarantined by macOS "
                     "(xattr -d com.apple.quarantine \"<path>\"), or unreadable.")
    else:
        lines.append("")
        lines.append("The architectures match, so something else is wrong. Check "
                     "that the file is readable, and that macOS has not "
                     "quarantined it:")
        lines.append(f'  xattr -l "{jvm_path}"')
    lines.append("")
    lines.append(f"Underlying error: {type(error).__name__}: {error}")
    return "\n".join(lines)


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

        try:
            jpype.startJVM(*args, jvmpath=jvm_path, classpath=jars)
        except Exception as exc:  # noqa: BLE001 - re-raised with a diagnosis
            raise RuntimeError(diagnose_jvm_failure(jvm_path, exc)) from exc

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
