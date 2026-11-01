"""
Tests for GameStateManager and ScoreManager.
Verifies mission switching, parameter validation, voting lifecycle, and scoring/badges.
"""

import pytest
from app.game.state import GameStateManager, MISSION_DEFINITIONS
from app.game.scoring import ScoreManager


def test_game_state_initialization():
    state = GameStateManager()
    assert state.active_mission_id == "mission_1"
    assert "energy_ev" in state.mission_params["mission_1"]
    assert state.active_physics_result["quantum_transmission"] > 0.0


def test_game_state_switch_mission():
    state = GameStateManager()
    assert state.set_active_mission("mission_2") is True
    assert state.active_mission_id == "mission_2"
    assert "wavelength_nm" in state.mission_params["mission_2"]
    # Invalid mission id must return False
    assert state.set_active_mission("invalid_mission_xyz") is False


def test_parameter_update_and_range_validation():
    state = GameStateManager()
    # Valid parameter within range
    assert state.update_parameter("energy_ev", 4.2) is True
    assert state.mission_params["mission_1"]["energy_ev"] == 4.2
    assert state.active_physics_result["energy_ev"] == 4.2

    # Out of range parameter should be rejected
    assert state.update_parameter("energy_ev", 999.0) is False
    assert state.update_parameter("energy_ev", -5.0) is False


def test_voting_lifecycle():
    state = GameStateManager()
    # Start voting round
    status = state.start_voting_round(duration_seconds=30)
    assert status["voting_open"] is True
    assert status["total_votes"] == 0

    # Record valid votes
    correct = state.get_mission_def()["default_question"]["correct_option"]
    wrong = next(o for o in state.get_mission_def()["default_question"]["options"] if o != correct)
    assert state.record_vote("viewer_1", correct) is True
    assert state.record_vote("viewer_2", correct) is True
    assert state.record_vote("viewer_3", wrong) is True

    # Reject invalid option
    assert state.record_vote("viewer_4", "Z") is False

    # Check status
    cur_status = state.get_voting_status()
    assert cur_status["total_votes"] == 3
    assert cur_status["tallies"][correct] == 2
    assert cur_status["tallies"][wrong] == 1

    # Resolve round
    res = state.close_and_resolve_voting()
    assert res["total_votes"] == 3
    assert "viewer_1" in res["correct_voters"]
    assert "viewer_2" in res["correct_voters"]
    assert "viewer_3" in res["incorrect_voters"]
    assert state.voting_open is False


def test_scoring_and_badge_award(tmp_path):
    import os
    test_path = str(tmp_path / "test_scores.json")
    if os.path.exists(test_path):
        os.remove(test_path)

    scores = ScoreManager(storage_path=test_path)
    correct = ["alice", "bob"]
    incorrect = ["charlie"]

    scores.record_prediction_round(
        mission_id="mission_1",
        correct_voters=correct,
        incorrect_voters=incorrect,
        badge_awarded_id="badge_quantum_explorer",
    )

    alice = scores.get_player_stats("alice")
    assert alice["points"] == 120  # 100 correct + 20 participation
    assert alice["current_streak"] == 1
    assert "badge_quantum_explorer" in alice["badges"]

    charlie = scores.get_player_stats("charlie")
    assert charlie["points"] == 20  # 20 participation
    assert charlie["current_streak"] == 0
    assert "badge_quantum_explorer" not in charlie["badges"]
