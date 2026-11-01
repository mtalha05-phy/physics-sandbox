"""
Twitch chat command parser, validator, and rate limiter.
Strictly parses commands, enforces numerical bounds, and protects against unauthorized injections.
"""

from typing import Dict, Any, Optional, Tuple
import math
import re
import time

# Commands that change the shared experiment for everybody. The server only honours them
# when ``is_mod_or_streamer`` is true (see app/main.py).
PRIVILEGED_ACTIONS = frozenset({"set_mission", "run_experiment", "start_round"})


def _finite_float(text: str) -> float:
    """float() that also rejects nan/inf, which float() happily accepts."""
    value = float(text)
    if not math.isfinite(value):
        raise ValueError("not finite")
    return value


class TwitchCommandParser:
    """Parses and validates Twitch chat messages into game actions."""

    def __init__(self, rate_limit_seconds: float = 1.0):
        self.rate_limit_seconds = rate_limit_seconds
        self.user_last_action_time: Dict[str, float] = {}

    def is_rate_limited(self, username: str) -> bool:
        now = time.time()
        if len(self.user_last_action_time) > 5000:  # bound memory: drop entries that no longer matter
            cutoff = now - self.rate_limit_seconds
            self.user_last_action_time = {u: t for u, t in self.user_last_action_time.items() if t > cutoff}
        last = self.user_last_action_time.get(username, 0.0)
        if now - last < self.rate_limit_seconds:
            return True
        self.user_last_action_time[username] = now
        return False

    def parse_message(
        self,
        username: str,
        raw_message: str,
        is_mod_or_streamer: bool = False,
    ) -> Optional[Dict[str, Any]]:
        """
        Parses a raw chat message. Returns a structured action dictionary or None if not a valid command.
        """
        msg = raw_message.strip()[:500]
        if not msg.startswith("!"):
            return None

        parts = msg.split()
        command = parts[0].lower()
        args = parts[1:]

        # 1. Prediction voting: !vote A / !vote B / !vote C / !vote D
        if command in ("!vote", "!v"):
            if not args:
                return {"type": "error", "message": "Usage: !vote <A|B|C|D>"}
            opt = args[0].upper()
            if opt in ("A", "B", "C", "D"):
                return {
                    "type": "vote",
                    "username": username,
                    "option": opt,
                }
            return {"type": "error", "message": f"Invalid vote option '{opt}'. Choose A, B, C, or D."}

        # Rate-limit non-vote commands to prevent spam
        if self.is_rate_limited(username):
            return {"type": "error", "message": "Please slow down your commands."}

        # 2. Help command: !help
        if command in ("!help", "!commands"):
            return {
                "type": "help",
                "username": username,
                "message": (
                    "ScienceQuest Live Commands: !vote <A-D> | !ask <question> | !score | "
                    "!energy <val> | !barrier <val> | !width <val> | !mission <1-5>"
                ),
            }

        # 3. Score inquiry: !score / !stats
        if command in ("!score", "!stats", "!points"):
            return {
                "type": "get_score",
                "username": username,
            }

        # 4. Leaderboard inquiry: !leaderboard / !top
        if command in ("!leaderboard", "!top"):
            return {
                "type": "get_leaderboard",
                "username": username,
            }

        # 5. Question to Quark: !ask <question>
        if command in ("!ask", "!quark", "!why"):
            question_text = " ".join(args).strip()
            if not question_text:
                return {"type": "error", "message": "Usage: !ask <your question about the experiment>"}
            # Truncate overly long prompts for security and cost control
            question_clean = question_text[:200]
            return {
                "type": "ask_quark",
                "username": username,
                "question": question_clean,
            }

        # 6. Mission selection: !mission <1-5>
        if command in ("!mission", "!m"):
            if not args:
                return {"type": "error", "message": "Usage: !mission <1-5>"}
            try:
                m_num = int(args[0])
                if 1 <= m_num <= 5:
                    return {
                        "type": "set_mission",
                        "username": username,
                        "mission_id": f"mission_{m_num}",
                        "is_mod_or_streamer": is_mod_or_streamer,
                    }
                return {"type": "error", "message": "Mission number must be between 1 and 5."}
            except ValueError:
                return {"type": "error", "message": "Invalid mission number."}

        # 7. Parameter adjustments: !energy <val>, !barrier <val>, !width <val>
        if command in ("!energy", "!e"):
            if not args:
                return {"type": "error", "message": "Usage: !energy <val in eV>"}
            try:
                val = _finite_float(args[0])
                return {"type": "set_param", "username": username, "param": "energy_ev", "value": val}
            except ValueError:
                return {"type": "error", "message": "Energy must be a valid number (eV)."}

        if command in ("!barrier", "!v0"):
            if not args:
                return {"type": "error", "message": "Usage: !barrier <val in eV>"}
            try:
                val = _finite_float(args[0])
                return {"type": "set_param", "username": username, "param": "barrier_height_ev", "value": val}
            except ValueError:
                return {"type": "error", "message": "Barrier height must be a valid number (eV)."}

        if command in ("!width", "!w"):
            if not args:
                return {"type": "error", "message": "Usage: !width <val in nm>"}
            try:
                val = _finite_float(args[0])
                return {"type": "set_param", "username": username, "param": "barrier_width_nm", "value": val}
            except ValueError:
                return {"type": "error", "message": "Barrier width must be a valid number (nm)."}

        # 8. Start experiment / start voting: !run, !start, !vote_start
        if command in ("!run", "!start", "!experiment"):
            return {
                "type": "run_experiment",
                "username": username,
                "is_mod_or_streamer": is_mod_or_streamer,
            }

        if command in ("!round", "!newround"):
            return {
                "type": "start_round",
                "username": username,
                "is_mod_or_streamer": is_mod_or_streamer,
            }

        return None
