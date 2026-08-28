"""Input validation for GTEM.

Fails fast, before the JVM starts, with a message that names the offending
parameter and states the acceptable range. The target user is a municipal
officer, not a programmer: a refusal to run is always better than a plausible
but wrong output folder.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any


class ConfigError(Exception):
    """Raised when a parameter or input file fails validation."""


# name -> (minimum, maximum, inclusive_min, inclusive_max, unit, why it matters)
NUMERIC_RULES: dict[str, tuple[float, float, bool, bool, str, str]] = {
    "dt": (0.0, 10.0, False, True, "seconds",
           "the timestep; above 10 s agents cross several links per tick and "
           "congestion is systematically under-counted"),
    "tsunami-eta": (0.0, 1440.0, False, True, "minutes",
                    "the wave arrival time; it bounds the whole run"),
    "departure-mean": (0.0, 240.0, True, True, "minutes",
                       "mean of the Rayleigh departure-time distribution"),
    "end-of-simulation": (0.0, 1440.0, True, True, "minutes",
                          "hard cut-off; 0 means 'use the tsunami ETA'"),
    "average-road-width": (0.0, 100.0, False, True, "metres",
                           "effective walkable width per lane"),
    "road-capacity-multiplier": (0.0, 100.0, False, True, "fraction or percent",
                                 "scales effective road width"),
    "max-snap-distance": (0.0, 5000.0, False, True, "metres",
                          "how far an agent may start from the road network"),
}

POPULATION_KEYS = ("total-adults", "total-elderly", "total-children")


def _as_number(name: str, value: Any) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        raise ConfigError(
            f"Parameter '{name}' must be a number, got {value!r}."
        ) from None


def validate_config(config: dict[str, Any]) -> None:
    """Raise ConfigError on the first invalid parameter."""
    errors: list[str] = []

    for name, (lo, hi, inc_lo, inc_hi, unit, why) in NUMERIC_RULES.items():
        if name not in config:
            continue
        value = _as_number(name, config[name])
        too_low = value < lo if inc_lo else value <= lo
        too_high = value > hi if inc_hi else value >= hi
        if too_low or too_high:
            lo_sym = "<=" if inc_lo else "<"
            hi_sym = "<=" if inc_hi else "<"
            errors.append(
                f"'{name}' = {value:g} {unit} is out of range. "
                f"Acceptable: {lo:g} {lo_sym} {name} {hi_sym} {hi:g}. "
                f"This is {why}."
            )

    for name in POPULATION_KEYS:
        if name not in config:
            continue
        value = _as_number(name, config[name])
        if value < 0:
            errors.append(f"'{name}' = {value:g} must be zero or greater.")
        if value != int(value):
            errors.append(f"'{name}' = {value:g} must be a whole number of people.")

    if all(k in config for k in POPULATION_KEYS):
        total = sum(_as_number(k, config[k]) for k in POPULATION_KEYS)
        if total <= 0:
            errors.append(
                "Total population is zero. Set at least one of "
                f"{', '.join(POPULATION_KEYS)} above zero."
            )

    low, high = config.get("vulnerability-low"), config.get("vulnerability-high")
    if low is not None and high is not None:
        low_v, high_v = _as_number("vulnerability-low", low), _as_number("vulnerability-high", high)
        if low_v >= high_v:
            errors.append(
                f"'vulnerability-low' ({low_v:g}) must be strictly less than "
                f"'vulnerability-high' ({high_v:g}); they are the two map thresholds in minutes."
            )

    d_low, d_high = config.get("density-low"), config.get("density-high")
    if d_low is not None and d_high is not None:
        d_low_v, d_high_v = _as_number("density-low", d_low), _as_number("density-high", d_high)
        if d_low_v >= d_high_v:
            errors.append(
                f"'density-low' ({d_low_v:g}) must be strictly less than "
                f"'density-high' ({d_high_v:g}); they are the two congestion "
                "thresholds in people per square metre."
            )

    # Checked here rather than at report time: an unknown language must stop the
    # run before it starts, not after ten minutes of simulation.
    language = config.get("language")
    if language is not None:
        from text_strings import normalise_language

        try:
            normalise_language(language)
        except ValueError as exc:
            errors.append(str(exc))

    if errors:
        raise ConfigError(
            "Invalid configuration:\n" + "\n".join(f"  - {e}" for e in errors)
        )


def validate_zone(base_dir: Path, zone: str) -> None:
    """Check that a zone folder has every layer GTEM needs, in a metric CRS."""
    zone_dir = Path(base_dir) / "data" / zone
    if not zone_dir.is_dir():
        raise ConfigError(
            f"Zone folder not found: {zone_dir}\n"
            f"  Expected a folder named '{zone}' inside data/."
        )

    # Only the DATA layers are required here. The route table is DERIVED, not
    # input: it lives in cache/ and is rebuilt on demand. Requiring it in
    # data/ would contradict the rule that data/ is never written to, and
    # would make a freshly prepared zone impossible to validate.
    required = {
        "zone boundary": zone_dir / f"{zone}.shp",
        "road network": zone_dir / f"rutas_{zone}.shp",
        "intersections": zone_dir / f"puntos_{zone}.shp",
        "census blocks": zone_dir / f"manzanas_{zone}.shp",
    }
    missing = [f"{label} ({path.name})" for label, path in required.items()
               if not path.is_file()]
    if missing:
        raise ConfigError(
            f"Zone '{zone}' is incomplete. Missing:\n"
            + "\n".join(f"  - {m}" for m in missing)
            + "\n  Run check_inputs.py for a full report on this folder."
        )

    _validate_crs(required["zone boundary"].with_suffix(".prj"), zone)


def _validate_crs(prj_path: Path, zone: str) -> None:
    """GTEM measures distances in metres; a geographic CRS breaks that."""
    if not prj_path.is_file():
        raise ConfigError(
            f"Zone '{zone}' has no .prj file ({prj_path.name}), so its coordinate "
            "reference system is unknown.\n"
            "  GTEM requires a PROJECTED, metric CRS (for example UTM). Assign one "
            "in QGIS and re-export."
        )
    text = prj_path.read_text(encoding="latin-1", errors="replace")
    if "PROJCS" not in text.upper():
        head = text.strip()[:80]
        raise ConfigError(
            f"Zone '{zone}' uses a geographic (lat/lon) CRS, not a projected one.\n"
            f"  Found: {head}...\n"
            "  Distances would be computed in DEGREES and every result would be "
            "meaningless. Reproject to a metric CRS (for example UTM zone 17S for "
            "Peru, or JGD2011 zone 10 for Sendai) and re-export."
        )


def assert_uniform_dt(rows: list[dict[str, Any]]) -> None:
    """Refuse to aggregate runs that used different timesteps."""
    seen = sorted({round(float(r["dt"]), 6) for r in rows if r.get("dt") is not None})
    if len(seen) > 1:
        raise ConfigError(
            "Refusing to aggregate runs with different timesteps: dt = "
            f"{', '.join(f'{v:g}' for v in seen)} s.\n"
            "  Congestion resolution depends on dt, so these runs are not "
            "comparable and must not share a summary table."
        )
