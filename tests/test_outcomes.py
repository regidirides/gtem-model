"""Outcome accounting, ETA behaviour and determinism, against the real engine.

They pin down the two properties most easily got wrong: nobody may be counted
safe after the wave arrives, and no one may be absent from the reported totals.
"""

from __future__ import annotations

import pytest

pytestmark = pytest.mark.engine


def outcomes(run):
    return {
        "evacuated": int(run.number("evacuees-safe")),
        "caught": int(run.number("caught-in-transit")),
        "stranded": int(run.number("stranded-agents")),
        "requested": int(run.number("agents-requested")),
    }


def test_every_agent_ends_in_exactly_one_outcome(engine):
    run = engine().populate().run_to_end()
    o = outcomes(run)
    assert o["evacuated"] + o["caught"] + o["stranded"] == o["requested"], (
        "outcomes do not account for every agent requested")
    assert o["requested"] == 300


def test_conservation_holds_at_several_arrival_times(engine):
    for eta in (5, 12, 23):
        run = engine(**{"tsunami-eta": eta}).populate().run_to_end()
        o = outcomes(run)
        assert o["evacuated"] + o["caught"] + o["stranded"] == o["requested"], (
            f"conservation failed at ETA {eta}")


def test_run_stops_exactly_at_the_arrival_time(engine):
    for eta in (5, 10, 23):
        run = engine(**{"tsunami-eta": eta}).populate().run_to_end()
        elapsed = run.number("ticks") * run.number("dt") / 60
        assert abs(elapsed - eta) < 1e-6, (
            f"ETA {eta} min but the run ended at {elapsed} min")


def test_impossibly_short_eta_saves_nobody(engine):
    """With less time than the fastest possible walk, evacuees must be zero."""
    run = engine(**{"tsunami-eta": 0.2, "departure-mean": 5}).populate().run_to_end()
    o = outcomes(run)
    assert o["evacuated"] == 0, "somebody reached safety in 12 seconds"
    assert o["caught"] + o["stranded"] == o["requested"]


def test_generous_eta_catches_nobody(engine):
    """Given enough time, nobody should still be walking."""
    run = engine(**{"tsunami-eta": 600, "departure-mean": 2}).populate().run_to_end()
    o = outcomes(run)
    assert o["caught"] == 0, f"{o['caught']} agents still walking after 10 hours"
    assert o["evacuated"] + o["stranded"] == o["requested"]


def test_evacuation_is_monotonic_in_the_arrival_time(engine):
    """More time can never save fewer people."""
    previous = -1
    for eta in (5, 10, 15, 23, 40):
        run = engine(**{"tsunami-eta": eta}).populate().run_to_end()
        evacuated = int(run.number("evacuees-safe"))
        assert evacuated >= previous, (
            f"ETA {eta} saved {evacuated}, fewer than the shorter ETA's {previous}")
        previous = evacuated


def test_same_seed_gives_identical_results(engine):
    first = engine(**{"input-seed": 4242}).populate().run_to_end()
    second = engine(**{"input-seed": 4242}).populate().run_to_end()
    assert outcomes(first) == outcomes(second)
    for series in ("history-evacuees", "history-moving", "history-speed"):
        assert ([float(x) for x in first.report(series)]
                == [float(x) for x in second.report(series)]), (
            f"{series} differs between two identical runs")


def test_different_seeds_give_different_results(engine):
    """Guards against a fixed seed silently forcing identical runs."""
    a = engine(**{"input-seed": 111}).populate().run_to_end()
    b = engine(**{"input-seed": 222}).populate().run_to_end()
    assert outcomes(a) != outcomes(b), (
        "two different seeds produced identical results; the seed may be ignored")


def test_a_terminal_record_exists_for_every_agent(engine):
    """The vulnerability map must contain non-evacuees, not only survivors."""
    run = engine().populate().run_to_end()
    records = run.report("vulnerability-origin-data")
    o = outcomes(run)
    assert len(records) == o["requested"]
    codes = [int(r[3]) for r in records]
    assert codes.count(1) == o["evacuated"]
    assert codes.count(2) == o["caught"]
    assert codes.count(3) == o["stranded"]
