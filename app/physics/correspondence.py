"""
Mission 5: The Classical-Quantum Boundary.
Models wave packet spreading, Ehrenfest's theorem, and the macroscopic correspondence limit.
"""

from dataclasses import dataclass
from typing import Dict, Any, List
import math
import numpy as np

from app.physics.constants import HBAR, ELECTRON_MASS


@dataclass
class CorrespondenceResult:
    mass_kg: float
    mass_description: str
    initial_width_m: float
    time_elapsed_s: float
    dispersion_timescale_s: float
    current_width_m: float
    spreading_factor: float

    # Trajectory comparison
    time_points_s: List[float]
    classical_center_m: List[float]
    quantum_width_m: List[float]
    quantum_upper_bound_m: List[float]
    quantum_lower_bound_m: List[float]

    # Scientific analysis
    is_classical_approximation_valid: bool
    domain_explanation: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "mass_kg": float(f"{self.mass_kg:.3e}"),
            "mass_description": self.mass_description,
            "initial_width_m": float(f"{self.initial_width_m:.3e}"),
            "time_elapsed_s": float(f"{self.time_elapsed_s:.3e}"),
            "dispersion_timescale_s": float(f"{self.dispersion_timescale_s:.3e}"),
            "current_width_m": float(f"{self.current_width_m:.3e}"),
            "spreading_factor": round(self.spreading_factor, 3),
            "is_classical_approximation_valid": self.is_classical_approximation_valid,
            "domain_explanation": self.domain_explanation,
            "time_points_s": [float(f"{t:.3e}") for t in self.time_points_s],
            "classical_center_m": [float(f"{x:.6e}") for x in self.classical_center_m],
            "quantum_width_m": [float(f"{w:.4e}") for w in self.quantum_width_m],
            "quantum_upper_bound_m": [float(f"{x:.6e}") for x in self.quantum_upper_bound_m],
            "quantum_lower_bound_m": [float(f"{x:.6e}") for x in self.quantum_lower_bound_m],
        }


def calculate_correspondence(
    object_preset: str = "electron",  # "electron", "buckyball", "dust_grain", "baseball"
    initial_velocity_mps: float = 10.0,
    time_elapsed_s: float = 1.0,
    custom_mass_kg: float = 0.0,
) -> CorrespondenceResult:
    """
    Simulates quantum wavepacket dispersion versus classical point particle trajectory.
    """
    presets = {
        "electron": {
            "mass": ELECTRON_MASS,
            "name": "Electron (Microscopic Quantum)",
            "width": 1e-10,  # 0.1 nm (atomic size)
            "typical_time": 1e-14,
        },
        "buckyball": {
            "mass": 720.0 * 1.6605390666e-27,  # C60 molecule ~ 1.2e-24 kg
            "name": "Fullerene C60 Buckyball (Mesoscopic)",
            "width": 1e-9,  # 1 nm
            "typical_time": 1e-5,
        },
        "dust_grain": {
            "mass": 1e-12,  # 1 nanogram (1e-12 kg)
            "name": "Dust Grain, 1 ng (Classical)",
            "width": 1e-6,  # 1 micrometer
            "typical_time": 1.0,
        },
        "baseball": {
            "mass": 0.145,  # 145 grams
            "name": "Baseball (Macroscopic Classical)",
            "width": 1e-3,  # 1 millimeter
            "typical_time": 1.0,
        },
    }

    if not math.isfinite(float(initial_velocity_mps)) or not math.isfinite(float(time_elapsed_s)):
        raise ValueError("initial_velocity_mps and time_elapsed_s must be finite")
    time_elapsed_s = min(max(0.0, float(time_elapsed_s)), 1.0e12)

    if isinstance(object_preset, str) and object_preset in presets:
        conf = presets[object_preset]
        mass = conf["mass"]
        name = conf["name"]
        w0 = conf["width"]
        t_eval = conf["typical_time"] if time_elapsed_s <= 0 else time_elapsed_s
    else:
        mass = max(1e-31, float(custom_mass_kg)) if custom_mass_kg > 0 else ELECTRON_MASS
        name = f"Custom Particle ({mass:.2e} kg)"
        w0 = 1e-9
        t_eval = time_elapsed_s

    # Timescale of wave packet spreading: tau = 2 * m * w0^2 / hbar
    tau = (2.0 * mass * (w0**2)) / HBAR

    # Width at time t: w(t) = w0 * sqrt(1 + (t / tau)^2)
    ratio = t_eval / tau if tau > 0 else float("inf")
    spreading_factor = math.sqrt(1.0 + (ratio**2))
    w_current = w0 * spreading_factor

    # Classical center trajectory: x(t) = x0 + v * t
    num_steps = 100
    t_arr = np.linspace(0.0, t_eval, num_steps)
    x_classical = initial_velocity_mps * t_arr

    # Quantum envelope bounds: x_cl +/- w(t)
    w_t_arr = w0 * np.sqrt(1.0 + (t_arr / tau) ** 2)
    x_upper = x_classical + w_t_arr
    x_lower = x_classical - w_t_arr

    # Validity criterion: if tau >> experiment time scale, spreading is negligible
    # and classical trajectory perfectly approximates quantum expectation value.
    is_classical_valid = tau > (100.0 * t_eval)

    if is_classical_valid:
        explanation = (
            f"For this mass ({mass:.2e} kg) the spreading timescale tau = 2 m w0^2 / hbar is {tau:.2e} s "
            f"(about {tau / 3.156e7:.1e} years), far longer than the observation time. Wavepacket spreading "
            f"is therefore unobservable and the centre of the packet follows the Newtonian trajectory."
        )
    else:
        explanation = (
            f"For this mass ({mass:.2e} kg) the spreading timescale is tau = {tau:.2e} s, comparable to or shorter "
            f"than the observation time. The packet has grown to {spreading_factor:.3g}x its initial width, so a "
            f"point-particle trajectory is not a good description and the full wavefunction is required."
        )

    return CorrespondenceResult(
        mass_kg=mass,
        mass_description=name,
        initial_width_m=w0,
        time_elapsed_s=t_eval,
        dispersion_timescale_s=tau,
        current_width_m=w_current,
        spreading_factor=spreading_factor,
        time_points_s=t_arr.tolist(),
        classical_center_m=x_classical.tolist(),
        quantum_width_m=w_t_arr.tolist(),
        quantum_upper_bound_m=x_upper.tolist(),
        quantum_lower_bound_m=x_lower.tolist(),
        is_classical_approximation_valid=is_classical_valid,
        domain_explanation=explanation,
    )
