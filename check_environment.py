"""Check that this machine can actually run GTEM.

Run this first, before anything else:

    python check_environment.py

It prints one line per requirement and, for anything missing or broken, the
exact command to fix it. Exit code 0 means GTEM can run; 1 means it cannot.

WHY THIS ACTUALLY IMPORTS EVERY PACKAGE
    Checking that a package is present on disk proves very little. A package can
    be installed and still fail to import - a matplotlib built against NumPy 1.x
    will not load under NumPy 2.x, for instance. Importing is the only check
    that means anything, so that is what this does.
"""
from __future__ import annotations

import sys
from pathlib import Path

# Library modules and the simulation engine live in src/.
sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))
import importlib
import platform
import sys
from pathlib import Path

from netlogo_runtime import (
    detect_netlogo_home,
    describe_environment,
    diagnose_jvm_failure as describe_jvm_failure,
    jvm_library_path,
    library_architectures,
)
from version import TESTED_JAVA, TESTED_NETLOGO, VERSION_STAMP

BASE_DIR = Path(__file__).resolve().parent

# import name -> (pip name, what GTEM uses it for)
PACKAGES: dict[str, tuple[str, str]] = {
    "numpy": ("numpy", "numerics"),
    "pandas": ("pandas", "tables and CSV output"),
    "matplotlib": ("matplotlib", "figures"),
    "networkx": ("networkx", "route pre-computation"),
    "pynetlogo": ("pynetlogo", "the bridge to the NetLogo engine"),
    "jpype": ("JPype1", "starting the Java virtual machine"),
    "fpdf": ("fpdf", "the PDF report"),
    "geopandas": ("geopandas", "input checking (check_inputs.py)"),
    "shapely": ("shapely", "geometry"),
    "pyproj": ("pyproj", "coordinate reference systems"),
    "pytest": ("pytest", "the test suite (developers only)"),
}

OPTIONAL = {"pytest"}

OK = "  [ OK ]"
BAD = "  [FAIL]"
WARN = "  [WARN]"


def check_packages() -> list[str]:
    """Import each package for real. Returns a list of remediation hints."""
    problems: list[str] = []
    for module, (pip_name, purpose) in PACKAGES.items():
        try:
            mod = importlib.import_module(module)
        except ImportError as exc:
            tag = WARN if module in OPTIONAL else BAD
            print(f"{tag} {module:<14} cannot be imported  ({purpose})")
            print(f"         {type(exc).__name__}: {exc}")
            if module not in OPTIONAL:
                problems.append(f"pip install {pip_name}")
            continue
        except Exception as exc:  # noqa: BLE001 - a broken build, not a missing one
            print(f"{BAD} {module:<14} INSTALLED BUT BROKEN  ({purpose})")
            print(f"         {type(exc).__name__}: {exc}")
            problems.append(
                f"pip install --force-reinstall {pip_name}   "
                f"# rebuilt against the installed numpy"
            )
            continue
        version = getattr(mod, "__version__", "unknown")
        print(f"{OK} {module:<14} {version:<12} ({purpose})")
    return problems


def check_netlogo() -> list[str]:
    problems: list[str] = []
    home = detect_netlogo_home()
    if home is None:
        print(f"{BAD} NetLogo        not found")
        for line in describe_environment().splitlines():
            print(f"         {line}")
        problems.append(
            "Install NetLogo "
            f"{TESTED_NETLOGO}, or set NETLOGO_HOME to its folder."
        )
        return problems

    print(f"{OK} NetLogo        {home}")
    jvm = jvm_library_path(home)
    if jvm is None:
        print(f"{BAD} JVM            no JVM library inside that NetLogo install")
        problems.append("Reinstall NetLogo; its bundled Java runtime is missing.")
        return problems

    # Presence is not enough - see the note at the top of this file. A JVM can
    # sit on disk and still refuse to load, most often because Python and the
    # runtime were built for different processors. Compare first, because the
    # comparison is instant and gives a far better message than a failed load.
    host = platform.machine()
    architectures = library_architectures(jvm)
    if architectures and host not in architectures:
        print(f"{BAD} JVM            {Path(jvm).name} is "
              f"{', '.join(architectures)}, but Python is {host}")
        print(f"         A {host} Python cannot load a "
              f"{'/'.join(architectures)} Java runtime.")
        problems.append(
            f"Recreate the environment with a {'/'.join(architectures)} Python "
            "(Miniforge is the simplest on Apple Silicon), then "
            "conda env create -f environment.yml")
        return problems

    detail = f" ({', '.join(architectures)})" if architectures else ""
    print(f"{OK} JVM            {Path(jvm).name}{detail}")

    # Then actually start it. This is the only check that proves the pair works.
    try:
        import jpype
        if not jpype.isJVMStarted():
            jpype.startJVM("-Djava.awt.headless=true", jvmpath=jvm)
        print(f"{OK} JVM starts     "
              f"Java {jpype.java.lang.System.getProperty('java.version')}")
    except Exception as exc:  # noqa: BLE001 - any failure here is a real problem
        print(f"{BAD} JVM starts     it will not load")
        for line in describe_jvm_failure(jvm, exc).splitlines():
            print(f"         {line}")
        problems.append("The Java runtime inside NetLogo will not load; see above.")
    return problems


def check_files() -> list[str]:
    problems: list[str] = []
    for label, path in (
        ("model", BASE_DIR / "src" / "gtem_model.nlogox"),
        ("data folder", BASE_DIR / "data"),
    ):
        if path.exists():
            print(f"{OK} {label:<14} {path.name}")
        else:
            print(f"{BAD} {label:<14} missing: {path}")
            problems.append(f"Restore {path.name} from the repository.")
    return problems


def main() -> int:
    print(f"{VERSION_STAMP} - environment check")
    print(f"  platform: {platform.system()} {platform.release()} ({platform.machine()})")
    print(f"  python:   {sys.version.split()[0]}")
    print(f"  tested against: NetLogo {TESTED_NETLOGO}, Java {TESTED_JAVA}")
    print()

    problems = check_packages() + check_netlogo() + check_files()

    print()
    if not problems:
        print("Everything needed is present. GTEM can run on this machine.")
        print("Next step:  python main.py --config examples/config_example.txt")
        return 0

    print(f"{len(problems)} problem(s) must be fixed before GTEM can run:")
    for i, hint in enumerate(problems, 1):
        print(f"  {i}. {hint}")
    print()
    print("The quickest way to get a known-good environment:")
    print("  conda env create -f environment.yml")
    print("  conda activate gtem")
    return 1


if __name__ == "__main__":
    sys.exit(main())
