"""The Rayleigh departure sampler must have the configured MEAN.

The model uses an inverse-CDF sampler. It is easy to write one whose parameter
is the Rayleigh SCALE rather than the mean; the two differ by a factor of
sqrt(pi/2) ~ 1.2533, which would silently shift every departure time by 25%.
"""

from __future__ import annotations

import math
import random
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def _model_path() -> Path:
    """Locate the engine in either the flat or the packaged layout."""
    for candidate in (ROOT / "src" / "gtem_model.nlogox", ROOT / "gtem_model.nlogox"):
        if candidate.is_file():
            return candidate
    return ROOT / "gtem_model.nlogox"


def rayleigh_inverse_cdf(probability: float, mean_seconds: float) -> float:
    """Python mirror of the model's reporter of the same name."""
    scale = mean_seconds * math.sqrt(2 / math.pi)
    return math.sqrt(-2 * scale ** 2 * math.log(1 - probability))


def test_model_formula_is_unchanged():
    """Guard the NetLogo implementation this mirror is checked against."""
    text = (_model_path()).read_text(encoding="utf-8")
    source = re.search(r"<code><!\[CDATA\[(.*?)\]\]></code>", text, re.S).group(1)
    body = source[source.index("to-report rayleigh-inverse-cdf"):]
    body = body[:body.index("end")]
    assert "sqrt (2 / pi )" in body.replace("  ", " ") or "sqrt (2 / pi)" in body
    assert "-2 * rayleigh-scale ^ 2 * ln(1 - probability)" in body.replace("  ", " ")


def test_sample_mean_matches_configured_mean():
    random.seed(20260810)
    for mean_minutes in (2.0, 5.0, 7.0, 12.0):
        mean_seconds = mean_minutes * 60
        draws = [rayleigh_inverse_cdf(random.random(), mean_seconds)
                 for _ in range(200_000)]
        sampled = sum(draws) / len(draws)
        relative_error = abs(sampled - mean_seconds) / mean_seconds
        assert relative_error < 0.01, (
            f"U={mean_minutes} min: sampled mean {sampled/60:.3f} min, "
            f"expected {mean_minutes} min ({relative_error:.2%} off). "
            "The parameter is probably the Rayleigh scale, not the mean.")


def test_parameter_is_the_mean_not_the_scale():
    """Explicitly reject the scale-vs-mean confusion."""
    random.seed(1)
    mean_seconds = 420.0
    draws = [rayleigh_inverse_cdf(random.random(), mean_seconds)
             for _ in range(200_000)]
    sampled = sum(draws) / len(draws)
    scale_interpretation = mean_seconds * math.sqrt(math.pi / 2)
    assert abs(sampled - mean_seconds) < abs(sampled - scale_interpretation)


def test_distribution_shape():
    """Rayleigh: median = scale*sqrt(2 ln 2), and it is right-skewed."""
    random.seed(2)
    mean_seconds = 420.0
    draws = sorted(rayleigh_inverse_cdf(random.random(), mean_seconds)
                   for _ in range(200_000))
    median = draws[len(draws) // 2]
    scale = mean_seconds * math.sqrt(2 / math.pi)
    assert abs(median - scale * math.sqrt(2 * math.log(2))) / median < 0.02
    assert median < sum(draws) / len(draws), "Rayleigh must be right-skewed"
