"""
Game state manager for the self-hosted *live* mode (Twitch / OBS).

The public website on Vercel does not use this class: serverless instances do not share memory,
so that edition keeps all state in the browser and calls the pure functions in ``app.solo``.
"""

from typing import Dict, Any, List, Optional
import math
import time

from app.game.missions import MISSION_DEFINITIONS, allowed_ranges  # noqa: F401  (re-exported)
from app.game.validation import ParamError, normalize_username, sanitize_param
from app.physics.tunneling import calculate_tunneling
from app.physics.double_slit import calculate_double_slit
from app.physics.uncertainty import calculate_uncertainty
from app.physics.wave_lab import calculate_wave_lab
from app.physics.correspondence import calculate_correspondence

MAX_VOTERS_PER_ROUND = 5000
MIN_ROUND_SECONDS = 5
MAX_ROUND_SECONDS = 300


def compute_physics(mission_id: str, params: Dict[str, Any]) -> Dict[str, Any]:
    """Pure function: run the physics engine of a mission for an already-validated parameter set."""
    if mission_id == "mission_1":
        return calculate_tunneling(
            energy_ev=params["energy_ev"],
            barrier_height_ev=params["barrier_height_ev"],
            barrier_width_nm=params["barrier_width_nm"],
            particle_mass_me=params["particle_mass_me"],
        ).to_dict()
    if mission_id == "mission_2":
        return calculate_double_slit(
            wavelength_nm=params["wavelength_nm"],
            slit_separation_um=params["slit_separation_um"],
            slit_width_um=params["slit_width_um"],
            screen_distance_m=params["screen_distance_m"],
            which_path_enabled=params["which_path_enabled"],
            which_path_strength=params["which_path_strength"],
            num_slits=params["num_slits"],
        ).to_dict()
    if mission_id == "mission_3":
        return calculate_uncertainty(
            sigma_x_nm=params["sigma_x_nm"],
            central_energy_ev=params["central_energy_ev"],
            packet_chirp=params["packet_chirp"],
        ).to_dict()
    if mission_id == "mission_4":
        return calculate_wave_lab(
            wavelength_m=params["wavelength_m"],
            amplitude_1=params["amplitude_1"],
            amplitude_2=params["amplitude_2"],
            phase_diff_deg=params["phase_diff_deg"],
            frequency_hz=params["frequency_hz"],
        ).to_dict()
    if mission_id == "mission_5":
        return calculate_correspondence(
            object_preset=params["object_preset"],
            initial_velocity_mps=params["initial_velocity_mps"],
            time_elapsed_s=params["time_elapsed_s"],
        ).to_dict()
    raise ParamError("Unknown mission")


class GameStateManager:
    """Live experiment state, parameters, physics results and voting rounds (single process)."""

    def __init__(self):
        self.active_mission_id: str = "mission_1"
        self.active_world: str = "quantum"
        self.mission_params: Dict[str, Dict[str, Any]] = {
            m_id: dict(m_info["default_params"]) for m_id, m_info in MISSION_DEFINITIONS.items()
        }
        self.active_physics_result: Dict[str, Any] = {}
        self.voting_open: bool = False
        self.voting_start_time: float = 0.0
        self.voting_duration_seconds: int = 45
        self.votes: Dict[str, str] = {}  # normalised (lower-case) username -> option letter
        self.last_round_result: Optional[Dict[str, Any]] = None
        self.is_simulating: bool = False
        self.round_resolved: bool = False  # guards against awarding the same votes twice
        self.round_id: int = 1
        self.recalculate_current_physics()

    # ------------------------------------------------------------------ missions / parameters
    def get_mission_def(self, mission_id: Optional[str] = None) -> Dict[str, Any]:
        return MISSION_DEFINITIONS.get(mission_id or self.active_mission_id, MISSION_DEFINITIONS["mission_1"])

    def set_active_mission(self, mission_id: str) -> bool:
        if mission_id not in MISSION_DEFINITIONS:
            return False
        self.active_mission_id = mission_id
        self.active_world = MISSION_DEFINITIONS[mission_id]["world"]
        self.voting_open = False
        self.round_resolved = False
        self.votes.clear()
        self.round_id += 1
        self.recalculate_current_physics()
        return True

    def update_parameter(self, param_name: Any, value: Any) -> bool:
        """Validate and apply one parameter. Invalid input leaves the state untouched."""
        try:
            clean = sanitize_param(self.active_mission_id, param_name, value)
        except ParamError:
            return False
        params = self.mission_params[self.active_mission_id]
        previous = params[param_name]
        params[param_name] = clean
        try:
            self.recalculate_current_physics()
        except Exception:  # never keep a value the physics engine cannot handle
            params[param_name] = previous
            self.recalculate_current_physics()
            return False
        return True

    def recalculate_current_physics(self) -> Dict[str, Any]:
        self.active_physics_result = compute_physics(
            self.active_mission_id, self.mission_params[self.active_mission_id]
        )
        return self.active_physics_result

    # ------------------------------------------------------------------ voting
    def _expire_if_needed(self) -> None:
        if self.voting_open and time.time() - self.voting_start_time >= self.voting_duration_seconds:
            self.voting_open = False

    def start_voting_round(self, duration_seconds: int = 45) -> Dict[str, Any]:
        try:
            duration = int(duration_seconds)
        except (TypeError, ValueError):
            duration = 45
        self.voting_duration_seconds = max(MIN_ROUND_SECONDS, min(MAX_ROUND_SECONDS, duration))
        self.voting_open = True
        self.round_resolved = False
        self.voting_start_time = time.time()
        self.votes.clear()
        self.round_id += 1
        return self.get_voting_status()

    def record_vote(self, username: Any, option: Any) -> bool:
        self._expire_if_needed()
        if not self.voting_open:
            return False
        key = normalize_username(username)
        if key is None or not isinstance(option, str):
            return False
        clean_option = option.strip().upper()
        if clean_option not in self.get_mission_def()["default_question"]["options"]:
            return False
        if key not in self.votes and len(self.votes) >= MAX_VOTERS_PER_ROUND:
            return False
        self.votes[key] = clean_option  # one vote per person; re-voting overwrites
        return True

    def get_voting_status(self) -> Dict[str, Any]:
        self._expire_if_needed()
        q_info = self.get_mission_def()["default_question"]
        tallies = {opt: 0 for opt in q_info["options"]}
        for opt in self.votes.values():
            tallies[opt] += 1
        total = len(self.votes)
        percentages = {o: (round(c / total * 100, 1) if total else 0.0) for o, c in tallies.items()}
        time_left = 0
        if self.voting_open:
            time_left = max(0, math.ceil(self.voting_duration_seconds - (time.time() - self.voting_start_time)))
        return {
            "round_id": self.round_id,
            "voting_open": self.voting_open,
            "time_remaining_seconds": time_left,
            "total_votes": total,
            "tallies": tallies,
            "percentages": percentages,
            "question": q_info["text"],
            "options": q_info["options"],
            "correct_option": q_info["correct_option"] if self.round_resolved else None,
        }

    def close_and_resolve_voting(self) -> Dict[str, Any]:
        self.voting_open = False
        already_resolved = self.round_resolved
        self.round_resolved = True
        q_info = self.get_mission_def()["default_question"]
        correct_option = q_info["correct_option"]
        tallies = {opt: 0 for opt in q_info["options"]}
        correct_voters: List[str] = []
        incorrect_voters: List[str] = []
        for user, opt in self.votes.items():
            tallies[opt] += 1
            (correct_voters if opt == correct_option else incorrect_voters).append(user)
        total = len(self.votes)
        percentages = {o: (round(c / total * 100, 1) if total else 0.0) for o, c in tallies.items()}
        consensus = max(tallies.items(), key=lambda item: item[1])[0] if total else None
        result = {
            "round_id": self.round_id,
            "mission_id": self.active_mission_id,
            "total_votes": total,
            "tallies": tallies,
            "percentages": percentages,
            "correct_option": correct_option,
            "consensus_option": consensus,
            "community_won": consensus == correct_option,
            "correct_voters": correct_voters,
            "incorrect_voters": incorrect_voters,
            "rationale": q_info["scientific_rationale"],
            "already_resolved": already_resolved,
        }
        self.last_round_result = result
        return result

    # ------------------------------------------------------------------ client payload
    def get_full_client_state(self) -> Dict[str, Any]:
        m_def = self.get_mission_def()
        return {
            "active_mission_id": self.active_mission_id,
            "active_world": self.active_world,
            "mission_title": m_def["title"],
            "mission_topic": m_def["topic"],
            "mission_description": m_def["description"],
            "allowed_ranges": allowed_ranges(self.active_mission_id),
            "controls": m_def["controls"],
            "current_params": self.mission_params[self.active_mission_id],
            "physics_result": self.active_physics_result,
            "voting_status": self.get_voting_status(),
            "last_round_result": self.last_round_result,
            "all_missions": [
                {"id": m["id"], "title": m["title"], "world": m["world"], "topic": m["topic"],
                 "badge_name": m["badge_name"], "difficulty": m["difficulty"]}
                for m in MISSION_DEFINITIONS.values()
            ],
        }
