"""Hostile-input tests. Each case below was accepted (and usually broke the server) before."""

import json
import math

import pytest

from app.game.state import GameStateManager
from app.game.validation import ParamError, normalize_username, sanitize_param, sanitize_params


@pytest.mark.parametrize("mission,key,value", [
    ("mission_1", "energy_ev", float("nan")),      # NaN passed "< min or > max" and poisoned shared state
    ("mission_1", "energy_ev", float("inf")),
    ("mission_1", "energy_ev", "abc"),             # strings bypassed the range check
    ("mission_1", "energy_ev", True),              # bool is an int subclass
    ("mission_1", "energy_ev", 11.0),
    ("mission_1", "energy_ev", None),
    ("mission_1", "nonexistent", 1.0),
    ("mission_2", "num_slits", 3),
    ("mission_2", "num_slits", "banana"),
    ("mission_2", "num_slits", 2.0),               # select values are strict (int, not float)
    ("mission_2", "which_path_enabled", "yes"),
    ("mission_2", "which_path_enabled", 1),
    ("mission_5", "object_preset", ["x"]),         # unhashable value crashed the physics call
    ("mission_5", "object_preset", "neutron_star"),
    ("mission_5", "time_elapsed_s", 1e300),        # overflow
    ("mission_5", "time_elapsed_s", -1.0),
    ("mission_4", "frequency_hz", "x"),
    ("mission_9", "energy_ev", 1.0),
    (None, "energy_ev", 1.0),
])
def test_rejects_bad_parameters(mission, key, value):
    with pytest.raises(ParamError):
        sanitize_param(mission, key, value)


def test_accepts_boundaries_and_typed_values():
    assert sanitize_param("mission_1", "energy_ev", 0.5) == 0.5
    assert sanitize_param("mission_1", "energy_ev", 10) == 10.0
    assert sanitize_param("mission_2", "num_slits", 1) == 1
    assert sanitize_param("mission_2", "which_path_enabled", True) is True
    assert sanitize_param("mission_5", "object_preset", "baseball") == "baseball"


def test_sanitize_params_rejects_unknown_keys_and_floods():
    with pytest.raises(ParamError):
        sanitize_params("mission_1", {"energy_ev": 3.0, "__proto__": 1})
    with pytest.raises(ParamError):
        sanitize_params("mission_1", {f"k{i}": 1 for i in range(100)})
    with pytest.raises(ParamError):
        sanitize_params("mission_1", [1, 2, 3])
    assert sanitize_params("mission_1", None)["energy_ev"] == 3.5


def test_state_survives_poison_attempts():
    g = GameStateManager()
    before = dict(g.mission_params["mission_1"])
    for bad in (float("nan"), "abc", float("inf"), None, [1], {"a": 1}, True):
        assert g.update_parameter("energy_ev", bad) is False
    assert g.mission_params["mission_1"] == before
    json.dumps(g.get_full_client_state(), allow_nan=False)   # Starlette serialises with allow_nan=False
    assert g.update_parameter("energy_ev", 4.0) is True


def test_every_mission_works_across_slider_extremes():
    """No slider combination within the advertised ranges may crash or produce NaN."""
    from app.game.missions import MISSION_DEFINITIONS
    from app.game.state import compute_physics
    for mid, m in MISSION_DEFINITIONS.items():
        sliders = [c for c in m["controls"] if c["kind"] == "slider"]
        for pick in ("min", "max"):
            params = dict(m["default_params"])
            params.update({c["key"]: c[pick] for c in sliders})
            result = compute_physics(mid, sanitize_params(mid, params))
            json.dumps(result, allow_nan=False)


@pytest.mark.parametrize("name,expected", [
    ("Alice", "alice"), ("  alice ", "alice"), ("ALICE", "alice"), ("a_1", "a_1"),
    ("<script>", None), ("", None), ("x" * 26, None), ("a b", None), (None, None), (5, None),
])
def test_normalize_username(name, expected):
    assert normalize_username(name) == expected


def test_case_variants_cannot_stuff_the_ballot():
    g = GameStateManager()
    g.start_voting_round(30)
    for variant in ("Alice", "alice", "ALICE", " alice", "aLiCe"):
        g.record_vote(variant, "A")
    assert g.get_voting_status()["total_votes"] == 1


def test_votes_after_deadline_are_rejected():
    g = GameStateManager()
    g.start_voting_round(30)
    g.voting_start_time -= 31          # the deadline passed and nobody polled the status meanwhile
    assert g.record_vote("late", "A") is False


def test_resolving_twice_is_flagged():
    g = GameStateManager()
    g.start_voting_round(30)
    assert g.close_and_resolve_voting()["already_resolved"] is False
    assert g.close_and_resolve_voting()["already_resolved"] is True


def test_voter_table_is_bounded():
    from app.game.state import MAX_VOTERS_PER_ROUND
    g = GameStateManager()
    g.start_voting_round(30)
    for i in range(MAX_VOTERS_PER_ROUND + 50):
        g.record_vote(f"u{i}", "A")
    assert len(g.votes) == MAX_VOTERS_PER_ROUND


def test_scoring_counts_one_person_once(tmp_path):
    from app.game.scoring import ScoreManager
    sm = ScoreManager(storage_path=str(tmp_path / "lb.json"))
    sm.record_prediction_round("mission_1", ["Alice", "alice", "ALICE"], [], "badge_quantum_explorer")
    assert len(sm.players) == 1
    assert next(iter(sm.players.values())).predictions_made == 1
    sm.record_prediction_round("mission_1", ["<img onerror=x>"], [], "badge_quantum_explorer")
    assert list(sm.players) == ["alice"]       # invalid names never become profiles


def test_answer_is_not_revealed_before_the_round_is_resolved():
    g = GameStateManager()
    assert g.get_full_client_state()["voting_status"]["correct_option"] is None   # used to leak on a fresh GET /api/state
    g.start_voting_round(30)
    assert g.get_voting_status()["correct_option"] is None
    g.close_and_resolve_voting()
    assert g.get_voting_status()["correct_option"] is not None
