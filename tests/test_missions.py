"""Quiz-design guarantees: no positional or length shortcut to the right answer."""

from collections import Counter

from app.game.missions import MISSION_DEFINITIONS, allowed_ranges, public_question


def test_correct_answer_is_not_always_the_same_letter():
    letters = Counter(m["default_question"]["correct_option"] for m in MISSION_DEFINITIONS.values())
    assert len(letters) >= 3, letters      # it used to be "A" for all five missions
    assert max(letters.values()) <= 2


def test_correct_answer_is_not_systematically_the_longest():
    longest = 0
    for m in MISSION_DEFINITIONS.values():
        q = m["default_question"]
        if max(q["options"], key=lambda k: len(q["options"][k])) == q["correct_option"]:
            longest += 1
    assert longest <= 2


def test_question_structure():
    for mid, m in MISSION_DEFINITIONS.items():
        q = m["default_question"]
        assert set(q["options"]) == {"A", "B", "C", "D"}, mid
        assert q["correct_option"] in q["options"], mid
        assert len(q["scientific_rationale"]) > 80, mid


def test_public_question_never_reveals_answer():
    for mid in MISSION_DEFINITIONS:
        pub = public_question(mid)
        assert set(pub) == {"text", "options"}


def test_defaults_lie_inside_their_own_ranges():
    for mid, m in MISSION_DEFINITIONS.items():
        for c in m["controls"]:
            default = m["default_params"][c["key"]]
            if c["kind"] == "slider":
                assert c["min"] <= default <= c["max"], (mid, c["key"])
            if c["kind"] == "select":
                assert default in [o["value"] for o in c["options"]], (mid, c["key"])
        assert set(allowed_ranges(mid)) <= set(m["default_params"])


def test_missions_two_and_five_have_the_controls_their_lessons_need():
    """Regression: the detector toggle and object selector existed only in the raw API, never in the UI."""
    keys2 = {c["key"] for c in MISSION_DEFINITIONS["mission_2"]["controls"]}
    keys5 = {c["key"] for c in MISSION_DEFINITIONS["mission_5"]["controls"]}
    assert {"which_path_enabled", "num_slits"} <= keys2
    assert "object_preset" in keys5


def test_no_unsupported_claims_in_text():
    blob = " ".join(str(m) for m in MISSION_DEFINITIONS.values()).lower()
    assert "millions of years" not in blob
    assert "picosecond" not in blob
    assert "instantaneous" not in blob
