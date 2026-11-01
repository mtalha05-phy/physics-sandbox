"""
Input validation for simulation parameters and player names.

Every path that can change an experiment (REST, WebSocket, Twitch chat, the stateless web API)
goes through ``sanitize_param`` / ``sanitize_params``. This closes the following classes of bug
that existed before:

* ``NaN`` slipped through the range check (``nan < min`` and ``nan > max`` are both False) and
  permanently poisoned the shared state, because Starlette refuses to serialise NaN.
* Non-numeric strings for slider parameters bypassed the range check entirely and crashed every
  later recalculation of that mission.
* Parameters that had no slider (``time_elapsed_s``, ``num_slits`` ...) accepted *any* value,
  including ``1e300`` (overflow) or unhashable lists.
* Booleans are ``int`` subclasses in Python, so ``True`` used to be accepted as the number 1.
"""

import math
import re
from typing import Any, Dict, Optional

from app.game.missions import MISSION_DEFINITIONS

MAX_PARAMS_PER_REQUEST = 16
MAX_STRING_LEN = 32

_USERNAME_RE = re.compile(r"^[A-Za-z0-9_]{1,25}$")


class ParamError(ValueError):
    """Raised when a parameter name or value is not acceptable."""


def _is_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def _spec_for(mission_id: str, key: str) -> Dict[str, Any]:
    mission = MISSION_DEFINITIONS.get(mission_id)
    if mission is None:
        raise ParamError("Unknown mission")
    for control in mission["controls"]:
        if control["key"] == key:
            return control
    hidden = mission.get("hidden_params", {})
    if key in hidden:
        return {"key": key, "kind": "number", "min": hidden[key]["min"], "max": hidden[key]["max"]}
    raise ParamError(f"Unknown parameter '{str(key)[:MAX_STRING_LEN]}'")


def sanitize_param(mission_id: str, key: Any, value: Any) -> Any:
    """Validate one parameter for a mission and return the cleaned value."""
    if not isinstance(key, str) or len(key) > MAX_STRING_LEN:
        raise ParamError("Parameter name must be a short string")
    spec = _spec_for(mission_id, key)
    kind = spec["kind"]

    if kind in ("slider", "number"):
        if not _is_number(value):
            raise ParamError(f"'{key}' must be a number")
        v = float(value)
        if not math.isfinite(v):
            raise ParamError(f"'{key}' must be a finite number")
        if v < spec["min"] or v > spec["max"]:
            raise ParamError(f"'{key}' must be between {spec['min']} and {spec['max']}")
        return v

    if kind == "toggle":
        if not isinstance(value, bool):
            raise ParamError(f"'{key}' must be true or false")
        return value

    if kind == "select":
        if isinstance(value, bool) or not isinstance(value, (str, int)):
            raise ParamError(f"'{key}' has an invalid value")
        for option in spec["options"]:
            if option["value"] == value and type(option["value"]) is type(value):
                return option["value"]
        raise ParamError(f"'{key}' has an invalid value")

    raise ParamError("Unsupported parameter type")  # pragma: no cover


def sanitize_params(mission_id: str, params: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    """Return a complete, validated parameter set: mission defaults overridden by ``params``."""
    mission = MISSION_DEFINITIONS.get(mission_id)
    if mission is None:
        raise ParamError("Unknown mission")
    out = dict(mission["default_params"])
    if params is None:
        return out
    if not isinstance(params, dict):
        raise ParamError("params must be an object")
    if len(params) > MAX_PARAMS_PER_REQUEST:
        raise ParamError("Too many parameters")
    for key, value in params.items():
        out[key] = sanitize_param(mission_id, key, value)
    return out


def normalize_username(name: Any) -> Optional[str]:
    """
    Canonical (lower-case) player key, or ``None`` if the name is not valid.

    Twitch logins are 1-25 characters from ``[A-Za-z0-9_]`` and are case-insensitive, so
    ``Alice``, ``ALICE`` and ``alice`` must be the same voter. Previously votes were keyed on the
    raw string, which let one person cast many votes and farm points through case or whitespace
    variants.
    """
    if not isinstance(name, str):
        return None
    cleaned = name.strip()
    if not _USERNAME_RE.match(cleaned):
        return None
    return cleaned.lower()
