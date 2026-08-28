"""End-to-end scale sanity against an analytically known answer.

The strongest check in the suite. A synthetic zone contains two straight
1,000 m corridors, one east-west and one north-south, each ending at a safe
zone. An adult at the free-flow speed covers 1,000 m in 1000 / 1.33 = 751.88 s
= 12.5313 min.

Unlike the geometry checks in test_scale.py, which validate the coordinate
TRANSFORM, this validates the whole chain: scale, timestep, speed and the
movement loop together. An error in any one of them shows up here.

The two corridors must also agree with each other, which is an end-to-end test
of isotropy rather than an inspection of the envelope arithmetic.
"""

from __future__ import annotations

import pytest

pytestmark = pytest.mark.engine

FREE_FLOW = 1.33          # m/s, the model's base-walking-speed
CORRIDOR = 1000.0         # m
EXPECTED_MINUTES = CORRIDOR / FREE_FLOW / 60      # 12.5313
TOLERANCE = 0.02          # 2%, as specified in the work brief


def _walk(engine, dt):
    run = engine(zone="Synthetic_Corridor", adults=20, elderly=0, children=0,
                 **{"dt": dt, "departure-mean": 0, "tsunami-eta": 30,
                    "end-of-simulation": 0})
    return run.populate().run_to_end()


def test_walking_time_matches_the_analytical_answer(engine):
    run = _walk(engine, dt=5)
    assert int(run.number("evacuees-safe")) == 20, "not everyone reached safety"
    elapsed = run.number("ticks") * run.number("dt") / 60
    error = abs(elapsed - EXPECTED_MINUTES) / EXPECTED_MINUTES
    assert error < TOLERANCE, (
        f"simulated {elapsed:.4f} min against an analytical {EXPECTED_MINUTES:.4f} "
        f"min ({error:.2%} off). Scale, dt, speed or the movement loop is wrong.")


def test_both_corridors_take_the_same_time(engine):
    """East-west and north-south must agree: the world must be isotropic."""
    run = _walk(engine, dt=5)
    records = run.report("vulnerability-origin-data")
    arrivals = [(float(r[1]), float(r[2])) for r in records if int(r[3]) == 1]
    assert len(arrivals) == 20

    midpoint = sorted(y for y, _ in arrivals)[len(arrivals) // 2]
    east = [t for y, t in arrivals if y < midpoint]
    north = [t for y, t in arrivals if y >= midpoint]
    assert east and north, "agents did not use both corridors"

    dt = run.number("dt")
    mean_east = sum(east) / len(east) * dt / 60
    mean_north = sum(north) / len(north) * dt / 60
    difference = abs(mean_east - mean_north) / EXPECTED_MINUTES
    assert difference < 0.01, (
        f"east-west {mean_east:.4f} min vs north-south {mean_north:.4f} min "
        f"({difference:.2%} apart). The world is anisotropic.")


def test_a_finer_timestep_converges_on_the_analytical_answer(engine):
    """Discretisation error must shrink with dt, confirming it is only that."""
    coarse = _walk(engine, dt=10)
    fine = _walk(engine, dt=2)
    error_coarse = abs(coarse.number("ticks") * 10 / 60 - EXPECTED_MINUTES)
    error_fine = abs(fine.number("ticks") * 2 / 60 - EXPECTED_MINUTES)
    assert error_fine <= error_coarse, (
        f"halving dt did not reduce the error ({error_fine:.4f} vs "
        f"{error_coarse:.4f} min); the discrepancy is not discretisation")
