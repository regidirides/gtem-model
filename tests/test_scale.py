"""The distance scale must be isotropic, unrounded, and HUD-independent.

Rounding the scale, or letting the two axes differ, would overstate distance and
make every agent walk correspondingly slower. These tests pin both down.

Pure Python: it recomputes the scale from the shapefile envelope and the world
geometry declared in the .nlogox, independently of the model's own arithmetic.
"""

from __future__ import annotations

import math
import re
import struct
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
def _model_path() -> Path:
    """Locate the engine in either the flat or the packaged layout."""
    for candidate in (ROOT / "src" / "gtem_model.nlogox", ROOT / "gtem_model.nlogox"):
        if candidate.is_file():
            return candidate
    return ROOT / "gtem_model.nlogox"


MODEL = _model_path()
ZONE = "Chimbote_Zona1"

TOLERANCE = 1e-9


def shapefile_extent(path: Path) -> tuple[float, float]:
    """Width and height in CRS units, from the .shp header bounding box."""
    with open(path, "rb") as handle:
        header = handle.read(100)
    x_min, y_min, x_max, y_max = struct.unpack("<4d", header[36:68])
    return x_max - x_min, y_max - y_min


def model_source() -> str:
    text = MODEL.read_text(encoding="utf-8")
    return re.search(r"<code><!\[CDATA\[(.*?)\]\]></code>", text, re.S).group(1)


def declared_constant(name: str) -> float:
    match = re.search(rf"set {re.escape(name)} (\d+(?:\.\d+)?)", model_source())
    assert match, f"{name} is not set to a literal in the model"
    return float(match.group(1))


def test_scale_is_isotropic_and_unrounded():
    """metres-per-patch must equal max(w/W, h/H) exactly, with no rounding."""
    width, height = shapefile_extent(ROOT / "data" / ZONE / f"{ZONE}.shp")
    draw_width = declared_constant("map-draw-width")
    draw_height = declared_constant("map-draw-height")

    scale_x = width / draw_width
    scale_y = height / draw_height
    expected = max(scale_x, scale_y)

    assert expected != math.ceil(expected), (
        "This zone happens to have an integer scale, so the test cannot "
        "distinguish rounded from unrounded. Pick another zone.")
    # The scale must be the exact value, not its ceiling.
    assert abs(expected - 4.8292385509707865) < 1e-9, (
        f"Reference scale changed: expected 4.82924, computed {expected}")


def test_envelope_uses_one_scale_on_both_axes():
    """Both envelope extents must derive from the SAME metres-per-patch."""
    source = model_source()
    assert "let envelope-width  (metres-per-patch * patch-width)" in source
    assert "let envelope-height (metres-per-patch * patch-height)" in source
    # Deriving them independently is what would let the two axes disagree.
    assert "real-width * patch-width / map-patch-width" not in source


def test_no_ceiling_in_scale_calculation():
    """The rounding that caused the 3.4% error must not come back."""
    source = model_source()
    code_lines = [line.split(";")[0] for line in source.splitlines()]
    assert not any("ceiling" in line for line in code_lines), (
        "ceiling() reappeared in executable code; the scale would be rounded")


def test_scale_does_not_depend_on_hud_margins():
    """Changing the video legend must not change how fast agents walk."""
    source = model_source()
    scale_block = source[source.index("to setup-world-scale"):
                         source.index("gis:set-world-envelope")]
    executable = "\n".join(line.split(";")[0] for line in scale_block.splitlines())
    for hud in ("video-margin-right", "video-margin-top", "video-map-max-pxcor"):
        assert f"/ {hud}" not in executable and f"- {hud}" not in executable.replace(
            f"set video-map-max-pxcor (max-pxcor - video-margin-right)", ""), (
            f"{hud} feeds the movement scale again")
    assert "map-draw-width" in executable and "map-draw-height" in executable


@pytest.mark.engine
def test_engine_reports_the_expected_scale(engine):
    """The running model must agree with the independent calculation."""
    width, height = shapefile_extent(ROOT / "data" / ZONE / f"{ZONE}.shp")
    run = engine()
    reported = run.number("metres-per-patch")
    expected = max(width / run.number("map-draw-width"),
                   height / run.number("map-draw-height"))
    assert abs(reported - expected) < TOLERANCE


@pytest.mark.engine
def test_engine_link_geometry_matches_true_lengths(engine):
    """link-length * metres-per-patch must equal the true length in metres.

    Checked over every link, split by orientation, so anisotropy would show up
    as an east-west versus north-south difference.
    """
    run = engine()
    scale = run.number("metres-per-patch")
    rows = run.report(
        "[ (list link-length cost (abs ([xcor] of end1 - [xcor] of end2)) "
        "(abs ([ycor] of end1 - [ycor] of end2))) ] of links")
    ratios_ew, ratios_ns = [], []
    for patch_length, true_length, dx, dy in rows:
        patch_length, true_length = float(patch_length), float(true_length)
        if patch_length <= 0 or true_length <= 0:
            continue
        ratio = patch_length * scale / true_length
        (ratios_ew if float(dx) > float(dy) else ratios_ns).append(ratio)

    assert ratios_ew and ratios_ns
    median_ew = sorted(ratios_ew)[len(ratios_ew) // 2]
    median_ns = sorted(ratios_ns)[len(ratios_ns) // 2]
    # Straight links should be exact; the sub-1.0 tail is road curvature
    # (cost follows the polyline, link-length is the straight line), so the
    # MEDIAN is the clean signal.
    assert abs(median_ew - 1.0) < 0.01, f"east-west scale error: {median_ew}"
    assert abs(median_ns - 1.0) < 0.01, f"north-south scale error: {median_ns}"
    assert abs(median_ew - median_ns) < 0.01, "world is anisotropic"
