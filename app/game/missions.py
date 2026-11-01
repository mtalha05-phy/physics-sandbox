"""
Mission catalogue for ScienceQuest.

Single source of truth for:
  * mission metadata (titles, worlds, badges)
  * every user-facing control (sliders, toggles, selects) and its valid range
  * the prediction question and its scientific rationale

Validation of incoming parameters is derived from the ``controls`` below
(see ``app.game.validation``), so the UI, the REST API and Twitch chat commands
can never disagree about what is allowed.

Quiz design notes
-----------------
* The correct option is deliberately NOT always "A" and is not systematically the
  longest option, so a player cannot score by position or by length alone.
  ``tests/test_missions.py`` enforces both properties.
* Question text must stay true for *every* slider setting. Anything that depends on a
  slider value (for example E < V0) is stated explicitly inside the question.
"""

from typing import Any, Dict, List


def _slider(key: str, label: str, lo: float, hi: float, step: float, unit: str = "") -> Dict[str, Any]:
    return {"key": key, "kind": "slider", "label": label, "min": lo, "max": hi, "step": step, "unit": unit}


def _toggle(key: str, label: str) -> Dict[str, Any]:
    return {"key": key, "kind": "toggle", "label": label}


def _select(key: str, label: str, options: List[Dict[str, Any]]) -> Dict[str, Any]:
    return {"key": key, "kind": "select", "label": label, "options": options}


MISSION_DEFINITIONS: Dict[str, Dict[str, Any]] = {
    "mission_1": {
        "id": "mission_1",
        "title": "The Impossible Wall",
        "world": "quantum",
        "badge_id": "badge_quantum_explorer",
        "badge_name": "Quantum Explorer",
        "difficulty": "Beginner to Intermediate",
        "topic": "Classical Mechanics vs Quantum Tunneling",
        "description": (
            "Investigate why a quantum particle can tunnel through an energy barrier that "
            "classical physics treats as impenetrable."
        ),
        "default_params": {
            "energy_ev": 3.5,
            "barrier_height_ev": 5.0,
            "barrier_width_nm": 0.45,
            "particle_mass_me": 1.0,
        },
        "controls": [
            _slider("energy_ev", "Particle energy E", 0.5, 10.0, 0.1, "eV"),
            _slider("barrier_height_ev", "Barrier height V0", 1.0, 12.0, 0.1, "eV"),
            _slider("barrier_width_nm", "Barrier width a", 0.1, 2.0, 0.05, "nm"),
            _slider("particle_mass_me", "Particle mass", 0.5, 5.0, 0.5, "m_e"),
        ],
        "hidden_params": {},
        "default_question": {
            "text": (
                "Consider the classically forbidden case E < V0 (for example a 3.5 eV electron meeting a "
                "5.0 eV barrier). Can the electron be found on the far side?"
            ),
            "options": {
                "A": "No: with E < V0 both classical and quantum mechanics give exactly zero transmission",
                "B": "Yes: the wave decays inside the barrier but a small, non-zero amplitude emerges",
                "C": "Yes: classical mechanics also predicts it passes through the barrier easily",
                "D": "Only if it first absorbs enough heat to rise above the barrier energy V0",
            },
            "correct_option": "B",
            "scientific_rationale": (
                "For E < V0 the Schrodinger equation has an exponentially decaying (evanescent) solution inside "
                "the barrier, psi ~ exp(-kappa x) with kappa = sqrt(2m(V0 - E))/hbar. Because the barrier is "
                "finite, some amplitude survives on the far side, so T > 0 (roughly T ~ exp(-2 kappa a)). "
                "Classical mechanics forbids the region because the kinetic energy E - V0 would be negative."
            ),
        },
    },
    "mission_2": {
        "id": "mission_2",
        "title": "Wave or Particle?",
        "world": "quantum",
        "badge_id": "badge_wave_detective",
        "badge_name": "Wave Detective",
        "difficulty": "Intermediate",
        "topic": "Wave-Particle Duality & Which-Path Decoherence",
        "description": (
            "Send particles through two slits, then switch on a which-path detector and watch the "
            "interference fringes disappear."
        ),
        "default_params": {
            "wavelength_nm": 0.5,
            "slit_separation_um": 2.5,
            "slit_width_um": 0.5,
            "screen_distance_m": 1.2,
            "which_path_enabled": False,
            "which_path_strength": 1.0,
            "num_slits": 2,
        },
        "controls": [
            _slider("wavelength_nm", "Wavelength", 0.1, 2.0, 0.05, "nm"),
            _slider("slit_separation_um", "Slit separation d", 1.0, 6.0, 0.5, "um"),
            _slider("slit_width_um", "Slit width w", 0.2, 1.5, 0.1, "um"),
            _slider("screen_distance_m", "Screen distance L", 0.5, 3.0, 0.1, "m"),
            _toggle("which_path_enabled", "Which-path detector"),
            _slider("which_path_strength", "Detector strength D (when ON)", 0.0, 1.0, 0.1, ""),
            _select("num_slits", "Open slits", [
                {"value": 2, "label": "Two slits"},
                {"value": 1, "label": "One slit"},
            ]),
        ],
        "hidden_params": {},
        "default_question": {
            "text": (
                "A detector now records which slit each particle passes through. "
                "What happens to the interference fringes on the screen?"
            ),
            "options": {
                "A": "They become twice as bright and noticeably sharper",
                "B": "They shift sideways by a fixed amount but stay just as sharp",
                "C": "They are unchanged, because merely watching a particle cannot change where it lands",
                "D": "They vanish, leaving the plain sum of the two single-slit patterns",
            },
            "correct_option": "D",
            "scientific_rationale": (
                "Recording which-path information makes the two alternatives distinguishable, so their phase "
                "relationship is lost (decoherence) and the interference cross-term 2 Re(psi1* psi2) vanishes. "
                "No human observer and no classical 'kick' is required, only a record in the environment. "
                "With partial information the fringe visibility falls as V = sqrt(1 - D^2) "
                "(Englert-Greenberger duality)."
            ),
        },
    },
    "mission_3": {
        "id": "mission_3",
        "title": "The Uncertainty Challenge",
        "world": "quantum",
        "badge_id": "badge_quantum_thinker",
        "badge_name": "Quantum Thinker",
        "difficulty": "Intermediate to Advanced",
        "topic": "Heisenberg's Uncertainty Principle",
        "description": (
            "Squeeze the spatial width of a quantum wavepacket and watch its momentum distribution "
            "broaden so that the product of the two widths never drops below hbar/2."
        ),
        "default_params": {
            "sigma_x_nm": 0.25,
            "central_energy_ev": 5.0,
            "packet_chirp": 0.0,
        },
        "controls": [
            _slider("sigma_x_nm", "Position spread sigma_x", 0.05, 1.5, 0.05, "nm"),
            _slider("central_energy_ev", "Central energy", 1.0, 20.0, 0.5, "eV"),
            _slider("packet_chirp", "Phase chirp", 0.0, 3.0, 0.1, ""),
        ],
        "hidden_params": {},
        "default_question": {
            "text": (
                "An electron's position uncertainty is reduced by a factor of 10. "
                "What must happen to its momentum uncertainty?"
            ),
            "options": {
                "A": "It must grow by a factor of about 10 or more, because dx * dp >= hbar/2",
                "B": "It shrinks by a factor of 10, because the electron is now better localised",
                "C": "It stays the same; the relation only limits how good our instruments are",
                "D": "It drops to exactly zero once the position is known precisely enough",
            },
            "correct_option": "A",
            "scientific_rationale": (
                "dx * dp >= hbar/2 is an intrinsic property of wave mechanics: position and momentum "
                "amplitudes are Fourier transforms of each other. A narrower position distribution therefore "
                "forces a broader momentum distribution (for an unchirped Gaussian, dp = hbar / (2 dx)). It is "
                "not a statement about measurement error."
            ),
        },
    },
    "mission_4": {
        "id": "mission_4",
        "title": "The Wave Laboratory",
        "world": "classical",
        "badge_id": "badge_wave_master",
        "badge_name": "Wave Master",
        "difficulty": "Beginner to Intermediate",
        "topic": "Superposition & Classical vs Quantum Waves",
        "description": (
            "Combine two waves with a chosen phase difference and compare the classical intensity with "
            "the quantum probability that comes from adding amplitudes."
        ),
        "default_params": {
            "wavelength_m": 1.0,
            "amplitude_1": 1.0,
            "amplitude_2": 1.0,
            "phase_diff_deg": 180.0,
            "frequency_hz": 1.0,
        },
        "controls": [
            _slider("wavelength_m", "Wavelength", 0.2, 3.0, 0.1, "m"),
            _slider("amplitude_1", "Amplitude 1", 0.0, 2.0, 0.1, "a.u."),
            _slider("amplitude_2", "Amplitude 2", 0.0, 2.0, 0.1, "a.u."),
            _slider("phase_diff_deg", "Phase difference", 0.0, 360.0, 15.0, "deg"),
        ],
        "hidden_params": {"frequency_hz": {"min": 0.1, "max": 1000.0}},
        "default_question": {
            "text": (
                "Two classical waves of equal amplitude meet with a phase difference of 180 degrees "
                "(pi radians). What is the amplitude of the resulting wave?"
            ),
            "options": {
                "A": "Twice the amplitude of a single wave (constructive interference)",
                "B": "Square root of two times the amplitude of a single wave (quadrature sum)",
                "C": "Zero, because the two waves cancel completely (destructive interference)",
                "D": "Half the amplitude of a single wave, shared between the two waves",
            },
            "correct_option": "C",
            "scientific_rationale": (
                "A_res^2 = A1^2 + A2^2 + 2 A1 A2 cos(phi). For A1 = A2 and phi = 180 degrees, cos(phi) = -1, so "
                "A_res = |A1 - A2| = 0. The same amplitude arithmetic, applied to probability amplitudes, "
                "is what produces quantum interference."
            ),
        },
    },
    "mission_5": {
        "id": "mission_5",
        "title": "The Classical-Quantum Boundary",
        "world": "battle",
        "badge_id": "badge_reality_explorer",
        "badge_name": "Reality Explorer",
        "difficulty": "Advanced",
        "topic": "The Correspondence Principle & Wavepacket Spreading",
        "description": (
            "Compare how fast a free wavepacket spreads for an electron, a molecule, a dust grain and a "
            "baseball, and see why Newtonian trajectories emerge for heavy objects."
        ),
        "default_params": {
            "object_preset": "electron",
            "initial_velocity_mps": 10.0,
            "time_elapsed_s": 0.0,
        },
        "controls": [
            _select("object_preset", "Object", [
                {"value": "electron", "label": "Electron"},
                {"value": "buckyball", "label": "C60 molecule"},
                {"value": "dust_grain", "label": "Dust grain"},
                {"value": "baseball", "label": "Baseball"},
            ]),
            _slider("initial_velocity_mps", "Initial velocity", 1.0, 100.0, 1.0, "m/s"),
        ],
        # time_elapsed_s = 0 means "use a typical observation time for the chosen object".
        "hidden_params": {"time_elapsed_s": {"min": 0.0, "max": 1.0e12}},
        "default_question": {
            "text": (
                "Why does a baseball never visibly show wavepacket spreading or double-slit "
                "interference in everyday life?"
            ),
            "options": {
                "A": "Quantum mechanics stops applying to any object heavier than about a gram",
                "B": "Gravity collapses the quantum wavefunction of every sufficiently heavy object",
                "C": "Its large mass makes spreading absurdly slow, and the environment washes out interference",
                "D": "Large objects are built from different fundamental particles than small ones",
            },
            "correct_option": "C",
            "scientific_rationale": (
                "A free Gaussian packet spreads on a timescale tau = 2 m sigma0^2 / hbar. For a 0.145 kg baseball "
                "with sigma0 = 1 mm this is about 3e27 s (roughly 1e20 years), vastly longer than the age of the "
                "universe, while for an electron confined to 0.1 nm it is about 2e-16 s. In addition, collisions "
                "with air molecules and photons decohere macroscopic superpositions far faster than any "
                "experiment can resolve. Quantum mechanics does not switch off: for heavy objects its "
                "expectation values obey Newton's laws (Ehrenfest theorem)."
            ),
        },
    },
}


def allowed_ranges(mission_id: str) -> Dict[str, Dict[str, Any]]:
    """Slider ranges for a mission, in the legacy ``allowed_ranges`` shape used by older clients."""
    out: Dict[str, Dict[str, Any]] = {}
    for c in MISSION_DEFINITIONS[mission_id]["controls"]:
        if c["kind"] == "slider":
            out[c["key"]] = {"min": c["min"], "max": c["max"], "step": c["step"], "unit": c["unit"]}
    return out


def public_question(mission_id: str) -> Dict[str, Any]:
    """The question as shown to players. Never includes the correct option."""
    q = MISSION_DEFINITIONS[mission_id]["default_question"]
    return {"text": q["text"], "options": dict(q["options"])}
