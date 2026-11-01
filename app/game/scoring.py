"""
Scoring and badge progression system for ScienceQuest Live.
Tracks viewer points, achievements, prediction streaks, and provides transparent leaderboards.
"""

from typing import Dict, Any, List, Set, Optional
from dataclasses import dataclass, field
import json
import os
import pathlib
import tempfile

from app.game.validation import normalize_username

MAX_PLAYERS = 10000

BADGE_METADATA = {
    "badge_quantum_explorer": {
        "id": "badge_quantum_explorer",
        "name": "Quantum Explorer",
        "description": "Mastered barrier penetration and the physics of quantum tunneling.",
        "icon": "⚡",
    },
    "badge_wave_detective": {
        "id": "badge_wave_detective",
        "name": "Wave Detective",
        "description": "Uncovered wave-particle duality and which-path quantum decoherence.",
        "icon": "🌊",
    },
    "badge_quantum_thinker": {
        "id": "badge_quantum_thinker",
        "name": "Quantum Thinker",
        "description": "Calculated Heisenberg uncertainty limits and conjugate momentum spreads.",
        "icon": "🧠",
    },
    "badge_wave_master": {
        "id": "badge_wave_master",
        "name": "Wave Master",
        "description": "Navigated wave superposition, destructive interference, and probability amplitudes.",
        "icon": "✨",
    },
    "badge_reality_explorer": {
        "id": "badge_reality_explorer",
        "name": "Reality Explorer",
        "description": "Proved why classical mechanics emerges from quantum foundations at macro scales.",
        "icon": "🌌",
    },
}


@dataclass
class PlayerProfile:
    username: str
    points: int = 0
    predictions_made: int = 0
    predictions_correct: int = 0
    current_streak: int = 0
    best_streak: int = 0
    badges: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "username": self.username,
            "points": self.points,
            "predictions_made": self.predictions_made,
            "predictions_correct": self.predictions_correct,
            "accuracy_pct": round((self.predictions_correct / self.predictions_made * 100), 1) if self.predictions_made > 0 else 0.0,
            "current_streak": self.current_streak,
            "best_streak": self.best_streak,
            "badges": self.badges,
        }


class ScoreManager:
    """Manages player progression, points, streaks, badges, and persistence."""

    def __init__(self, storage_path: Optional[str] = None):
        if storage_path:
            self.storage_path = storage_path
        else:
            self.storage_path = os.environ.get("SCORES_PATH", "data/leaderboard.json")
        self.players: Dict[str, PlayerProfile] = {}
        self.ensure_storage_dir()
        self.load_from_disk()

    def ensure_storage_dir(self):
        try:
            p = pathlib.Path(self.storage_path).parent
            p.mkdir(parents=True, exist_ok=True)
        except Exception:
            pass

    def load_from_disk(self):
        if os.path.exists(self.storage_path):
            try:
                with open(self.storage_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    for u, pdata in data.items():
                        self.players[u] = PlayerProfile(
                            username=u,
                            points=pdata.get("points", 0),
                            predictions_made=pdata.get("predictions_made", 0),
                            predictions_correct=pdata.get("predictions_correct", 0),
                            current_streak=pdata.get("current_streak", 0),
                            best_streak=pdata.get("best_streak", 0),
                            badges=pdata.get("badges", []),
                        )
            except Exception:
                # If file read fails, keep memory store
                pass

    def save_to_disk(self):
        try:
            self.ensure_storage_dir()
            data = {u: p.to_dict() for u, p in self.players.items()}
            directory = os.path.dirname(os.path.abspath(self.storage_path))
            fd, tmp_path = tempfile.mkstemp(dir=directory, suffix=".tmp")
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
            os.replace(tmp_path, self.storage_path)  # atomic: a crash never leaves a half-written file
        except Exception:
            pass

    def get_or_create_player(self, username: str) -> Optional[PlayerProfile]:
        u_clean = normalize_username(username)
        if u_clean is None:
            return None
        if u_clean not in self.players:
            if len(self.players) >= MAX_PLAYERS:
                return None
            self.players[u_clean] = PlayerProfile(username=u_clean)
        return self.players[u_clean]

    def record_prediction_round(
        self,
        mission_id: str,
        correct_voters: List[str],
        incorrect_voters: List[str],
        badge_awarded_id: Optional[str] = None,
    ):
        """Awards points and badges to viewers based on prediction results."""
        seen = set()
        # Correct voters
        for username in correct_voters:
            p = self.get_or_create_player(username)
            if p is None or p.username in seen:
                continue
            seen.add(p.username)
            p.predictions_made += 1
            p.predictions_correct += 1
            p.current_streak += 1
            p.best_streak = max(p.best_streak, p.current_streak)

            # Base points: +100 for correct, +20 for participation, +15 streak bonus
            streak_bonus = (p.current_streak - 1) * 15
            p.points += 120 + streak_bonus

            if badge_awarded_id and badge_awarded_id in BADGE_METADATA:
                if badge_awarded_id not in p.badges:
                    p.badges.append(badge_awarded_id)

        # Incorrect voters
        for username in incorrect_voters:
            p = self.get_or_create_player(username)
            if p is None or p.username in seen:
                continue
            seen.add(p.username)
            p.predictions_made += 1
            p.current_streak = 0
            # Participation points: +20
            p.points += 20

        self.save_to_disk()

    def get_leaderboard(self, top_n: int = 10) -> List[Dict[str, Any]]:
        sorted_players = sorted(
            self.players.values(),
            key=lambda p: (p.points, p.predictions_correct),
            reverse=True,
        )
        return [p.to_dict() for p in sorted_players[:top_n]]

    def get_player_stats(self, username: str) -> Optional[Dict[str, Any]]:
        u_clean = normalize_username(username)
        if u_clean is not None and u_clean in self.players:
            return self.players[u_clean].to_dict()
        return None
