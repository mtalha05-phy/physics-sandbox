"""The stateless engine behind the Vercel website."""

import json

import pytest

from app import solo
from app.game.validation import ParamError


def test_catalog_hides_answers():
    cat = solo.catalog()
    assert len(cat["missions"]) == 5
    text = json.dumps(cat)
    assert "correct_option" not in text and "scientific_rationale" not in text


def test_build_state_is_deterministic_and_json_safe():
    a = solo.build_state("mission_1", {"energy_ev": 4.0})
    b = solo.build_state("mission_1", {"energy_ev": 4.0})
    assert a == b
    json.dumps(a, allow_nan=False)
    assert a["current_params"]["energy_ev"] == 4.0
    assert "voting_status" not in a and "correct_option" not in json.dumps(a)


def test_state_is_independent_between_callers():
    """No shared global state: one visitor's parameters never leak into another's."""
    first = solo.build_state("mission_1", {"energy_ev": 9.0})
    second = solo.build_state("mission_1", {})
    assert first["current_params"]["energy_ev"] == 9.0
    assert second["current_params"]["energy_ev"] == 3.5


def test_mission_five_presets_use_their_own_timescales():
    electron = solo.build_state("mission_5", {"object_preset": "electron"})["physics_result"]
    ball = solo.build_state("mission_5", {"object_preset": "baseball"})["physics_result"]
    assert electron["spreading_factor"] > 10
    assert ball["spreading_factor"] < 1.0001


@pytest.mark.parametrize("bad", [{"energy_ev": float("nan")}, {"energy_ev": "x"}, {"zzz": 1}, {"energy_ev": 99}])
def test_build_state_rejects_bad_params(bad):
    with pytest.raises(ParamError):
        solo.build_state("mission_1", bad)


def test_unknown_mission_rejected():
    for bad in ("mission_99", None, 5, ["mission_1"]):
        with pytest.raises(ParamError):
            solo.build_state(bad, {})


def test_check_answer():
    ok = solo.check_answer("mission_1", "b")
    assert ok["correct"] is True and ok["correct_option"] == "B"
    assert solo.check_answer("mission_1", "A")["correct"] is False
    with pytest.raises(ParamError):
        solo.check_answer("mission_1", "Z")
    with pytest.raises(ParamError):
        solo.check_answer("mission_1", 1)


def test_quark_prompt_helpers():
    from app.ai.quark import clean_question, summarise_physics
    st = solo.build_state("mission_1")["physics_result"]
    summary = summarise_physics(st)
    assert all(not isinstance(v, list) for v in summary.values())
    assert len(json.dumps(summary)) < 2000 < len(json.dumps(st))   # arrays were bloating every prompt
    assert clean_question("a\x00b\nc" + "x" * 500).count("\x00") == 0
    assert len(clean_question("x" * 500)) == 200
