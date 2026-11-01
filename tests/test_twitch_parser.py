"""
Unit tests for Twitch chat command parsing, parameter validation, and rate limiting.
"""

import pytest
from app.twitch.parser import TwitchCommandParser


def test_parse_valid_vote_commands():
    parser = TwitchCommandParser()
    res_a = parser.parse_message("curious_viewer", "!vote A")
    assert res_a["type"] == "vote"
    assert res_a["option"] == "A"

    res_b = parser.parse_message("quantum_fan", "!v B")
    assert res_b["type"] == "vote"
    assert res_b["option"] == "B"


def test_parse_invalid_vote_option():
    parser = TwitchCommandParser()
    res = parser.parse_message("viewer1", "!vote Z")
    assert res["type"] == "error"


def test_parse_parameter_adjustment():
    parser = TwitchCommandParser()
    res = parser.parse_message("viewer2", "!energy 4.5")
    assert res["type"] == "set_param"
    assert res["param"] == "energy_ev"
    assert res["value"] == 4.5


def test_parse_malformed_parameter():
    parser = TwitchCommandParser()
    res = parser.parse_message("viewer3", "!energy not_a_number")
    assert res["type"] == "error"


def test_parse_ask_quark():
    parser = TwitchCommandParser()
    res = parser.parse_message("einstein_jr", "!ask Why does quantum tunneling happen?")
    assert res["type"] == "ask_quark"
    assert "quantum tunneling" in res["question"]


def test_rate_limiting():
    parser = TwitchCommandParser(rate_limit_seconds=2.0)
    # First action should succeed
    res1 = parser.parse_message("spammer", "!energy 5.0")
    assert res1["type"] == "set_param"
    # Immediate second non-vote action should be rate limited
    res2 = parser.parse_message("spammer", "!barrier 6.0")
    assert res2["type"] == "error"
    assert "slow down" in res2["message"]
