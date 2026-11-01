"""
Mission 4: The Wave Laboratory - Classical Waves vs Quantum Interference.
Models classical wave superposition, constructive/destructive interference,
and compares with quantum probability amplitude interference.
"""

from dataclasses import dataclass
from typing import Dict, Any, List
import math
import numpy as np


@dataclass
class WaveLabResult:
    wavelength_m: float
    frequency_hz: float
    amplitude_1: float
    amplitude_2: float
    phase_diff_rad: float
    phase_diff_deg: float

    # Classical outcomes
    interference_type: str  # "constructive", "destructive", "intermediate"
    resultant_amplitude: float
    classical_intensity: float

    # Spatial wave snapshots along x in [-2*lambda, 2*lambda]
    x_grid: List[float]
    wave1_values: List[float]
    wave2_values: List[float]
    superposed_values: List[float]

    # Quantum comparison
    quantum_prob_1: float
    quantum_prob_2: float
    quantum_prob_interference: float
    quantum_cross_term: float

    def to_dict(self) -> Dict[str, Any]:
        return {
            "wavelength_m": round(self.wavelength_m, 3),
            "frequency_hz": round(self.frequency_hz, 2),
            "amplitude_1": round(self.amplitude_1, 3),
            "amplitude_2": round(self.amplitude_2, 3),
            "phase_diff_rad": round(self.phase_diff_rad, 4),
            "phase_diff_deg": round(self.phase_diff_deg, 1),
            "interference_type": self.interference_type,
            "resultant_amplitude": round(self.resultant_amplitude, 3),
            "classical_intensity": round(self.classical_intensity, 3),
            "x_grid": [round(x, 4) for x in self.x_grid],
            "wave1_values": [round(float(v), 4) for v in self.wave1_values],
            "wave2_values": [round(float(v), 4) for v in self.wave2_values],
            "superposed_values": [round(float(v), 4) for v in self.superposed_values],
            "quantum_prob_1": round(self.quantum_prob_1, 4),
            "quantum_prob_2": round(self.quantum_prob_2, 4),
            "quantum_prob_interference": round(self.quantum_prob_interference, 4),
            "quantum_cross_term": round(self.quantum_cross_term, 4),
        }


def calculate_wave_lab(
    wavelength_m: float = 1.0,
    amplitude_1: float = 1.0,
    amplitude_2: float = 1.0,
    phase_diff_deg: float = 0.0,
    frequency_hz: float = 1.0,
    num_points: int = 200,
) -> WaveLabResult:
    """
    Computes classical wave superposition and quantum probability amplitude comparison.
    """
    wavelength_m = max(0.1, float(wavelength_m))
    amplitude_1 = max(0.0, float(amplitude_1))
    amplitude_2 = max(0.0, float(amplitude_2))
    phase_rad = math.radians(phase_diff_deg % 360.0)

    # Resultant amplitude: A_res^2 = A1^2 + A2^2 + 2 A1 A2 cos(phi)
    res_amp_sq = (amplitude_1 ** 2) + (amplitude_2 ** 2) + 2.0 * amplitude_1 * amplitude_2 * math.cos(phase_rad)
    res_amp = math.sqrt(max(0.0, res_amp_sq))
    intensity = res_amp ** 2

    # Classify interference
    cos_val = math.cos(phase_rad)
    if cos_val > 0.95:
        int_type = "Strongly Constructive"
    elif cos_val < -0.95:
        int_type = "Strongly Destructive"
    elif cos_val > 0.3:
        int_type = "Partially Constructive"
    elif cos_val < -0.3:
        int_type = "Partially Destructive"
    else:
        int_type = "Quadrature (Independent Addition)"

    # Spatial wave profile at t = 0
    k = 2.0 * np.pi / wavelength_m
    x_span = 2.0 * wavelength_m
    x_arr = np.linspace(-x_span, x_span, num_points)

    w1 = amplitude_1 * np.sin(k * x_arr)
    w2 = amplitude_2 * np.sin(k * x_arr + phase_rad)
    w_net = w1 + w2

    # Quantum comparison:
    # Treat amplitudes as probability amplitudes: psi1, psi2
    # P_1 = |psi1|^2, P_2 = |psi2|^2
    # P_total = |psi1 + psi2|^2 = P1 + P2 + 2 * sqrt(P1 * P2) * cos(phi)
    # Cross term is unique quantum interference effect between probability amplitudes!
    p1 = amplitude_1 ** 2
    p2 = amplitude_2 ** 2
    cross_term = 2.0 * amplitude_1 * amplitude_2 * math.cos(phase_rad)
    p_total = p1 + p2 + cross_term

    return WaveLabResult(
        wavelength_m=wavelength_m,
        frequency_hz=frequency_hz,
        amplitude_1=amplitude_1,
        amplitude_2=amplitude_2,
        phase_diff_rad=phase_rad,
        phase_diff_deg=phase_diff_deg,
        interference_type=int_type,
        resultant_amplitude=res_amp,
        classical_intensity=intensity,
        x_grid=x_arr.tolist(),
        wave1_values=w1.tolist(),
        wave2_values=w2.tolist(),
        superposed_values=w_net.tolist(),
        quantum_prob_1=p1,
        quantum_prob_2=p2,
        quantum_prob_interference=p_total,
        quantum_cross_term=cross_term,
    )
