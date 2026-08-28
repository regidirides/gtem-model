"""Load and resolve a GTEM run configuration from an external file.

No user should ever edit Python source to change a parameter. The file format
is deliberately the simplest thing that works, because the reader may be a
municipal officer with no programming background:

    # comments start with a hash
    zone            = Chimbote_Zona1
    adults          = 11328
    tsunami_eta     = 23

Blank lines and comments are ignored, keys are case-insensitive, and both
``=`` and ``:`` separate a key from its value.

A copy of the resolved configuration is written into every run's output folder,
so a result can always be traced back to the exact settings that produced it.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from validation import ConfigError

#: config key -> (NetLogo/internal parameter name, python type, default)
#: A default of ``None`` means the key is required.
SCHEMA: dict[str, tuple[str, type, Any]] = {
    "zone":                   ("input-zone",               str,   None),
    "adults":                 ("total-adults",             int,   None),
    "elderly":                ("total-elderly",            int,   None),
    "children":               ("total-children",           int,   None),
    "departure_mean":         ("departure-mean",           float, 7.0),
    "tsunami_eta":            ("tsunami-eta",              float, None),
    "end_of_simulation":      ("end-of-simulation",        float, 0.0),
    "dt":                     ("dt",                       float, 10.0),
    "road_width":             ("average-road-width",       float, 2.8),
    "capacity_multiplier":    ("road-capacity-multiplier", float, 1.0),
    "max_snap_distance":      ("max-snap-distance",        float, 50.0),
    "vulnerability_low":      ("vulnerability-low",        float, 11.0),
    "vulnerability_high":     ("vulnerability-high",       float, 17.0),
    "density_low":            ("density-low",              float, 0.3),
    "density_high":           ("density-high",             float, 3.0),
    "seed":                   ("seed",                     int,   0),
    "recompute_routes":       ("recompute_routes",         bool,  False),
    "time_margin_analysis":   ("time_margin_analysis",     bool,  False),
    "record_video":           ("record_video",             bool,  False),
    "video_name":             ("video_name",               str,   "run.mp4"),
    "language":               ("language",                 str,   "en"),
}

#: Keys that configure Python, not the NetLogo model. The single source of
#: truth: both drivers import this rather than keeping their own copy. Three
#: copies of this set once existed, and adding a key to one of them left the
#: other two pushing an unknown global into NetLogo, which fails the run at
#: setup with "Nothing named X has been defined".
#:
#: Named by the resolved parameter name (the second column of SCHEMA), because
#: that is what the drivers iterate over.
PYTHON_ONLY = {
    "seed", "recompute_routes", "record_video", "video_name",
    "time_margin_analysis", "language",
    "vulnerability-low", "vulnerability-high", "density-low", "density-high",
    # Added by the batch driver, not by load_config.
    "run_id",
}

_TRUE = {"true", "yes", "y", "1", "on"}
_FALSE = {"false", "no", "n", "0", "off"}


def _coerce(key: str, raw: str, target: type) -> Any:
    text = raw.strip()
    if target is bool:
        low = text.lower()
        if low in _TRUE:
            return True
        if low in _FALSE:
            return False
        raise ConfigError(
            f"'{key}' must be true or false, got {raw!r}."
        )
    if target is str:
        return text
    try:
        value = float(text)
    except ValueError:
        raise ConfigError(
            f"'{key}' must be a number, got {raw!r}."
        ) from None
    if target is int:
        if value != int(value):
            raise ConfigError(
                f"'{key}' must be a whole number, got {raw!r}."
            )
        return int(value)
    return value


def load_config(path: str | Path) -> dict[str, Any]:
    """Parse a config file and return the resolved parameter dictionary."""
    path = Path(path)
    if not path.is_file():
        raise ConfigError(
            f"Configuration file not found: {path}\n"
            "  Copy examples/config_example.txt and edit it, then run:\n"
            f"    python main.py --config {path.name}"
        )

    seen: dict[str, str] = {}
    for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        stripped = line.split("#", 1)[0].strip()
        if not stripped:
            continue
        for sep in ("=", ":"):
            if sep in stripped:
                key, _, value = stripped.partition(sep)
                break
        else:
            raise ConfigError(
                f"{path.name} line {number}: cannot read {line.strip()!r}.\n"
                "  Expected  key = value"
            )
        key = key.strip().lower()
        if key not in SCHEMA:
            close = [k for k in SCHEMA if k.startswith(key[:4])]
            hint = f" Did you mean: {', '.join(close)}?" if close else ""
            raise ConfigError(
                f"{path.name} line {number}: unknown setting '{key}'.{hint}\n"
                f"  Valid settings: {', '.join(sorted(SCHEMA))}"
            )
        if key in seen:
            raise ConfigError(f"{path.name} line {number}: '{key}' is set twice.")
        seen[key] = value

    missing = [k for k, (_, _, default) in SCHEMA.items()
               if default is None and k not in seen]
    if missing:
        raise ConfigError(
            f"{path.name} is missing required settings: {', '.join(sorted(missing))}"
        )

    resolved: dict[str, Any] = {}
    for key, (param, target, default) in SCHEMA.items():
        resolved[param] = _coerce(key, seen[key], target) if key in seen else default
    return resolved


def write_resolved_copy(config: dict[str, Any], output_dir: str | Path) -> Path:
    """Write the resolved configuration into the run folder, verbatim."""
    from version import VERSION_STAMP

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    destination = output_dir / "resolved_config.txt"

    reverse = {param: key for key, (param, _, _) in SCHEMA.items()}
    lines = [
        f"# Resolved configuration for this run — {VERSION_STAMP}",
        "# Written automatically. Every setting actually used is listed here,",
        "# including defaults that were not present in the original file.",
        "",
    ]
    for param, value in config.items():
        lines.append(f"{reverse.get(param, param):<22} = {value}")
    destination.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return destination
