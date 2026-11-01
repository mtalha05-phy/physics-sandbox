"""
Stateless "solo" engine used by the public website (Vercel).

Why stateless: Vercel runs each request in whichever function instance is free, and instances do not
share memory. The browser therefore owns the player's state (mission, parameters, progress) and sends
what it needs with every request; the server only does validated, deterministic physics.

Everything here is a pure function of its arguments, free of web-framework code, and is covered by
``tests/test_solo.py``.
"""

from functools import lru_cache
from typing import Any, Dict, Optional, Tuple

from app.game.missions import MISSION_DEFINITIONS, allowed_ranges, public_question
from app.game.scoring import BADGE_METADATA
from app.game.state import compute_physics
from app.game.validation import ParamError, sanitize_params


def _mission(mission_id: Any) -> Dict[str, Any]:
    if not isinstance(mission_id, str) or mission_id not in MISSION_DEFINITIONS:
        raise ParamError("Unknown mission")
    return MISSION_DEFINITIONS[mission_id]


def _summary(m: Dict[str, Any]) -> Dict[str, Any]:
    return {"id": m["id"], "title": m["title"], "world": m["world"], "topic": m["topic"],
            "badge_id": m["badge_id"], "badge_name": m["badge_name"], "difficulty": m["difficulty"]}


def catalog() -> Dict[str, Any]:
    """Everything the client needs up front. The correct answers are never included."""
    return {
        "missions": [
            {**_summary(m), "description": m["description"], "default_params": dict(m["default_params"]),
             "controls": m["controls"], "question": public_question(m["id"])}
            for m in MISSION_DEFINITIONS.values()
        ],
        "badges": BADGE_METADATA,
    }


@lru_cache(maxsize=512)
def _cached_physics(mission_id: str, frozen_params: Tuple[Tuple[str, Any], ...]) -> Dict[str, Any]:
    return compute_physics(mission_id, dict(frozen_params))


def build_state(mission_id: Any, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Validated physics result and UI metadata for one mission and parameter set."""
    mission = _mission(mission_id)
    clean = sanitize_params(mission_id, params)
    physics = _cached_physics(mission_id, tuple(sorted(clean.items())))
    return {
        "active_mission_id": mission_id,
        "active_world": mission["world"],
        "mission_title": mission["title"],
        "mission_topic": mission["topic"],
        "mission_description": mission["description"],
        "allowed_ranges": allowed_ranges(mission_id),
        "controls": mission["controls"],
        "current_params": clean,
        "physics_result": physics,
        "question": public_question(mission_id),
        "all_missions": [_summary(m) for m in MISSION_DEFINITIONS.values()],
    }


def check_answer(mission_id: Any, option: Any) -> Dict[str, Any]:
    """Grade one answer. Returns the explanation together with the verdict."""
    mission = _mission(mission_id)
    q = mission["default_question"]
    if not isinstance(option, str) or option.strip().upper() not in q["options"]:
        raise ParamError("Invalid option")
    chosen = option.strip().upper()
    return {
        "correct": chosen == q["correct_option"],
        "chosen_option": chosen,
        "correct_option": q["correct_option"],
        "rationale": q["scientific_rationale"],
        "badge_id": mission["badge_id"],
        "badge_name": mission["badge_name"],
    }
