"""Bad configuration must be refused by name, before anything runs."""

from __future__ import annotations

from pathlib import Path

import pytest

from config import load_config
from validation import ConfigError, assert_uniform_dt, validate_config, validate_zone

ROOT = Path(__file__).resolve().parent.parent

VALID = {
    "dt": 10, "tsunami-eta": 23, "departure-mean": 7, "end-of-simulation": 30,
    "average-road-width": 2.8, "road-capacity-multiplier": 1,
    "max-snap-distance": 50, "total-adults": 2000, "total-elderly": 400,
    "total-children": 700, "vulnerability-low": 11, "vulnerability-high": 17,
    "density-low": 0.3, "density-high": 3,
}


def test_the_reference_configuration_is_accepted():
    validate_config(dict(VALID))


@pytest.mark.parametrize("key,value,expected_in_message", [
    ("dt", 0, "dt"),
    ("dt", 30, "dt"),                       # exceeds the model's own slider max
    ("dt", -5, "dt"),
    ("tsunami-eta", 0, "tsunami-eta"),
    ("tsunami-eta", -1, "tsunami-eta"),
    ("total-adults", -5, "total-adults"),
    ("total-adults", 10.5, "total-adults"),  # fractional people
    ("average-road-width", 0, "average-road-width"),
    ("road-capacity-multiplier", 0, "road-capacity-multiplier"),
])
def test_invalid_values_are_rejected_by_name(key, value, expected_in_message):
    config = dict(VALID)
    config[key] = value
    with pytest.raises(ConfigError) as caught:
        validate_config(config)
    assert expected_in_message in str(caught.value)


def test_zero_total_population_is_rejected():
    config = dict(VALID, **{"total-adults": 0, "total-elderly": 0,
                            "total-children": 0})
    with pytest.raises(ConfigError, match="population"):
        validate_config(config)


def test_inverted_thresholds_are_rejected():
    with pytest.raises(ConfigError, match="vulnerability-low"):
        validate_config(dict(VALID, **{"vulnerability-low": 20}))
    with pytest.raises(ConfigError, match="density-low"):
        validate_config(dict(VALID, **{"density-low": 5}))


def test_message_states_the_acceptable_range():
    with pytest.raises(ConfigError) as caught:
        validate_config(dict(VALID, dt=30))
    message = str(caught.value)
    assert "0 < dt <= 10" in message
    assert "timestep" in message


def test_mixed_timesteps_cannot_be_aggregated():
    with pytest.raises(ConfigError, match="different timesteps"):
        assert_uniform_dt([{"dt": 10}, {"dt": 5}])
    assert_uniform_dt([{"dt": 10}, {"dt": 10}])


def test_missing_zone_is_rejected():
    with pytest.raises(ConfigError, match="not found"):
        validate_zone(ROOT, "No_Such_Zone")


def test_incomplete_zone_is_rejected(tmp_path):
    """A zone folder missing a required layer must be refused by name."""
    zone = "Half_Built"
    folder = tmp_path / "data" / zone
    folder.mkdir(parents=True)
    # Only the boundary is present; roads, points and blocks are absent.
    (folder / f"{zone}.shp").write_bytes(b"")
    (folder / f"{zone}.prj").write_text('PROJCS["fake",UNIT["Metre",1]]')
    with pytest.raises(ConfigError, match="incomplete") as caught:
        validate_zone(tmp_path, zone)
    message = str(caught.value)
    assert "road network" in message and "census blocks" in message


def test_reference_zone_is_accepted():
    validate_zone(ROOT, "Chimbote_Zona1")


def test_example_config_parses_and_validates():
    config = load_config(ROOT / "examples" / "config_example.txt")
    validate_config(config)
    assert config["departure-mean"] == 7.0, "reference-paper default must be 7"


def test_unknown_setting_is_rejected_with_a_suggestion(tmp_path):
    path = tmp_path / "c.txt"
    path.write_text("zone = Chimbote_Zona1\nadults = 10\nelderly = 1\n"
                    "children = 1\ntsunami_eta = 20\ndeparture_meen = 7\n")
    with pytest.raises(ConfigError) as caught:
        load_config(path)
    assert "departure_meen" in str(caught.value)
    assert "Did you mean" in str(caught.value)


def test_duplicate_setting_is_rejected(tmp_path):
    path = tmp_path / "c.txt"
    path.write_text("zone = A\nzone = B\n")
    with pytest.raises(ConfigError, match="set twice"):
        load_config(path)


def test_missing_required_setting_is_rejected(tmp_path):
    path = tmp_path / "c.txt"
    path.write_text("zone = Chimbote_Zona1\n")
    with pytest.raises(ConfigError, match="missing required"):
        load_config(path)
