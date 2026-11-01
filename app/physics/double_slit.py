"""
Mission 2: Wave or Particle? - Double-Slit Experiment.

Fraunhofer (far-field) model of slits of width ``w`` and separation ``d``:

    single-slit envelope   E(y) = sinc^2(beta),   beta  = pi w y / (lambda L)
    two-path pattern       P(y) = E(y) * (1 + V cos(2 alpha)) / 2,   alpha = pi d y / (lambda L)

with fringe visibility V:
* coherent two slits:        V = 1  (P = E cos^2(alpha))
* which-path info D in 0..1: V = sqrt(1 - D^2)  (Englert-Greenberger duality, pure states);
                             D = 1 gives the incoherent sum of two identical single-slit patterns
* one slit:                  P = E

Removed earlier behaviour: the incoherent pattern was built from envelopes shifted by +/- d/2 on the
screen (about 1 um on a mm-scale screen). In the far field the two single-slit patterns are identical,
so the shift had no physical meaning. Visibility was hard-coded (1.0/0.0) and the fringe count came
from a 300-point peak search that aliased for fine fringes; both are now analytic.

Validity: far field needs L >> w^2/lambda (worst case (1.5 um)^2/0.1 nm = 22.5 mm vs L >= 0.5 m) and the
small-angle approximation holds because the screen half-width (5 mm) << L.
"""

from dataclasses import dataclass
from typing import Any, Dict, List
import math

import numpy as np


@dataclass
class DoubleSlitResult:
    wavelength_nm: float
    slit_separation_um: float
    slit_width_um: float
    screen_distance_m: float
    which_path_enabled: bool
    which_path_strength: float
    num_slits: int

    screen_positions_mm: List[float]
    classical_intensity: List[float]         # classical WAVE intensity (coherent interference)
    classical_particle_pattern: List[float]  # classical PARTICLES: sum of single-slit patterns
    quantum_probability: List[float]         # detection probability incl. which-path decoherence
    fringes_peak_count: int
    visibility: float
    fringe_spacing_mm: float

    def to_dict(self) -> Dict[str, Any]:
        return {
            "wavelength_nm": round(self.wavelength_nm, 3),
            "slit_separation_um": round(self.slit_separation_um, 3),
            "slit_width_um": round(self.slit_width_um, 3),
            "screen_distance_m": round(self.screen_distance_m, 3),
            "which_path_enabled": self.which_path_enabled,
            "which_path_strength": round(self.which_path_strength, 3),
            "num_slits": self.num_slits,
            "screen_positions_mm": [round(y, 3) for y in self.screen_positions_mm],
            "classical_intensity": [round(float(v), 5) for v in self.classical_intensity],
            "classical_particle_pattern": [round(float(v), 5) for v in self.classical_particle_pattern],
            "quantum_probability": [round(float(v), 5) for v in self.quantum_probability],
            "fringes_peak_count": self.fringes_peak_count,
            "visibility": round(self.visibility, 4),
            "fringe_spacing_mm": round(self.fringe_spacing_mm, 5),
        }


def _normalised(arr: np.ndarray) -> np.ndarray:
    peak = float(np.max(arr))
    return arr / peak if peak > 0 else arr


def calculate_double_slit(
    wavelength_nm: float = 0.5,
    slit_separation_um: float = 2.0,
    slit_width_um: float = 0.4,
    screen_distance_m: float = 1.0,
    which_path_enabled: bool = False,
    num_slits: int = 2,
    num_points: int = 800,
    screen_span_mm: float = 5.0,
    which_path_strength: float = 1.0,
) -> DoubleSlitResult:
    for name, val in (("wavelength_nm", wavelength_nm), ("slit_separation_um", slit_separation_um),
                      ("slit_width_um", slit_width_um), ("screen_distance_m", screen_distance_m),
                      ("which_path_strength", which_path_strength)):
        if not math.isfinite(float(val)):
            raise ValueError(f"{name} must be finite")

    lam_m = max(1e-12, float(wavelength_nm) * 1e-9)
    d_m = max(1e-9, float(slit_separation_um) * 1e-6)
    w_m = max(1e-9, float(slit_width_um) * 1e-6)
    L_m = max(1e-3, float(screen_distance_m))
    strength = min(1.0, max(0.0, float(which_path_strength)))
    two_slits = int(num_slits) != 1

    y_mm = np.linspace(-screen_span_mm, screen_span_mm, num_points)
    sin_theta = (y_mm * 1e-3) / L_m
    beta = np.pi * w_m * sin_theta / lam_m
    envelope = np.sinc(beta / np.pi) ** 2
    alpha = np.pi * d_m * sin_theta / lam_m

    if not two_slits:
        visibility = 0.0
    else:
        distinguishability = strength if which_path_enabled else 0.0
        visibility = math.sqrt(max(0.0, 1.0 - distinguishability ** 2))

    classical_wave = envelope * np.cos(alpha) ** 2 if two_slits else envelope
    quantum = envelope * (1.0 + visibility * np.cos(2.0 * alpha)) / 2.0 if two_slits else envelope

    spacing_m = lam_m * L_m / d_m
    peaks = 0
    if two_slits and visibility >= 0.1:
        m_max = min(int(math.floor((screen_span_mm * 1e-3) / spacing_m)), 5000)
        for m in range(-m_max, m_max + 1):
            b = math.pi * w_m * (m * spacing_m / L_m) / lam_m
            env = 1.0 if b == 0 else (math.sin(b) / b) ** 2
            if env >= 0.05:
                peaks += 1

    return DoubleSlitResult(
        wavelength_nm=float(wavelength_nm),
        slit_separation_um=float(slit_separation_um),
        slit_width_um=float(slit_width_um),
        screen_distance_m=float(screen_distance_m),
        which_path_enabled=bool(which_path_enabled),
        which_path_strength=strength,
        num_slits=2 if two_slits else 1,
        screen_positions_mm=y_mm.tolist(),
        classical_intensity=_normalised(classical_wave).tolist(),
        classical_particle_pattern=_normalised(envelope).tolist(),
        quantum_probability=_normalised(quantum).tolist(),
        fringes_peak_count=peaks,
        visibility=visibility,
        fringe_spacing_mm=spacing_m * 1e3,
    )
