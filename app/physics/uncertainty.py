"""
Mission 3: The Uncertainty Challenge - Heisenberg Uncertainty Principle.
Mathematically models Gaussian wavepackets in position and momentum spaces.
Verifies Delta x * Delta p >= hbar / 2.
"""

from dataclasses import dataclass
from typing import Dict, Any, List
import math
import numpy as np

from app.physics.constants import HBAR, ELECTRON_MASS


@dataclass
class UncertaintyResult:
    sigma_x_nm: float
    p0_momentum_si: float
    state_purity_factor: float  # >= 1.0 (1.0 for ideal minimum-uncertainty packet)

    # Calculated statistical uncertainties
    delta_x_m: float
    delta_x_nm: float
    delta_p_si: float
    uncertainty_product: float
    hbar_over_two: float
    ratio_to_minimum: float  # 1.0 for an unchirped Gaussian, sqrt(1 + C^2) when chirped
    is_minimum_uncertainty: bool

    # Spatial distribution
    x_grid_nm: List[float]
    psi_prob_density_x: List[float]
    psi_real_x: List[float]

    # Momentum distribution (in units of 10^-24 kg*m/s)
    p_grid_scaled: List[float]
    phi_prob_density_p: List[float]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "sigma_x_nm": round(self.sigma_x_nm, 4),
            "delta_x_nm": round(self.delta_x_nm, 4),
            "delta_p_si": float(f"{self.delta_p_si:.4e}"),
            "uncertainty_product": float(f"{self.uncertainty_product:.4e}"),
            "hbar_over_two": float(f"{self.hbar_over_two:.4e}"),
            "ratio_to_minimum": round(self.ratio_to_minimum, 4),
            "is_minimum_uncertainty": abs(self.ratio_to_minimum - 1.0) < 1e-4,
            "x_grid_nm": [round(x, 4) for x in self.x_grid_nm],
            "psi_prob_density_x": [round(float(p), 5) for p in self.psi_prob_density_x],
            "psi_real_x": [round(float(p), 5) for p in self.psi_real_x],
            "p_grid_scaled": [round(float(p), 4) for p in self.p_grid_scaled],
            "phi_prob_density_p": [round(float(p), 5) for p in self.phi_prob_density_p],
        }


def calculate_uncertainty(
    sigma_x_nm: float = 0.2,       # spatial packet width in nm
    central_energy_ev: float = 5.0, # sets central momentum p0
    packet_chirp: float = 0.0,      # chirp factor >= 0 (causes product > hbar/2)
    num_points: int = 250,
) -> UncertaintyResult:
    """
    Computes position and momentum representations of a normalized 1D wave packet.
    """
    for _name, _val in (('sigma_x_nm', sigma_x_nm), ('central_energy_ev', central_energy_ev),
                        ('packet_chirp', packet_chirp)):
        if not math.isfinite(float(_val)):
            raise ValueError(f'{_name} must be finite')
    central_energy_ev = max(0.01, float(central_energy_ev))
    packet_chirp = max(0.0, float(packet_chirp))
    sigma_x_nm = max(0.02, min(5.0, float(sigma_x_nm)))
    sigma_x_m = sigma_x_nm * 1e-9

    # Energy to central momentum p0 = sqrt(2 m E)
    e_joules = central_energy_ev * 1.602176634e-19
    p0 = math.sqrt(2.0 * ELECTRON_MASS * e_joules)

    # Minimum momentum width: sigma_p0 = hbar / (2 * sigma_x)
    sigma_p_ideal = HBAR / (2.0 * sigma_x_m)

    # Chirped Gaussian: psi(x) ~ exp(-a x^2) with a = 1/(4 sigma_x^2) - i b.
    # Its momentum variance is  sigma_k^2 = |a|^2 / Re(a) = (1/(4 sigma_x^2)) * (1 + 16 b^2 sigma_x^4),
    # so  delta_p = sigma_p_ideal * sqrt(1 + 16 b^2 sigma_x^4).
    # We define the dimensionless chirp C = 4 b sigma_x^2, i.e. b = C / (4 sigma_x^2), which gives
    #   delta_p = sigma_p_ideal * sqrt(1 + C^2)
    # (The previous code used b = C / (2 sigma_x^2) in the plotted phase but sqrt(1 + C^2) for delta_p,
    #  which understated the true momentum spread by up to a factor of 2 at C = 3.)
    purity_factor = math.sqrt(1.0 + (packet_chirp ** 2))
    delta_p = sigma_p_ideal * purity_factor
    delta_x = sigma_x_m

    product = delta_x * delta_p
    hbar_2 = HBAR / 2.0
    ratio = product / hbar_2

    # Spatial grid spanning [-4*sigma_x, +4*sigma_x]
    span_x_nm = max(4.0 * sigma_x_nm, 0.5)
    x_nm = np.linspace(-span_x_nm, span_x_nm, num_points)
    x_m = x_nm * 1e-9

    # Wavefunction in position space:
    # Normalized: (1 / (2 pi sigma_x^2))^(1/4) * exp(-x^2 / (4 sigma_x^2)) * exp(i k0 x)
    norm_x = (1.0 / (2.0 * np.pi * (sigma_x_m**2))) ** 0.25
    envelope_x = np.exp(-(x_m**2) / (4.0 * (sigma_x_m**2)))
    k0 = p0 / HBAR
    psi_x_complex = norm_x * envelope_x * np.exp(1j * (k0 * x_m + (packet_chirp / (4 * sigma_x_m**2)) * (x_m**2)))
    rho_x = np.abs(psi_x_complex) ** 2
    # Normalize for display plotting
    rho_x_plot = rho_x / np.max(rho_x)
    psi_real_plot = np.real(psi_x_complex) / np.max(np.abs(psi_x_complex))

    # Momentum grid spanning [-4*delta_p, +4*delta_p] around p0
    span_p = 4.0 * delta_p
    p_arr = np.linspace(p0 - span_p, p0 + span_p, num_points)
    # Unit scale for momentum: 10^-24 kg*m/s for readability
    p_scale = 1e-24
    p_grid_scaled = (p_arr - p0) / p_scale

    # Momentum probability distribution: Gaussian centered at p0 with std delta_p
    norm_p = 1.0 / (math.sqrt(2.0 * np.pi) * delta_p)
    rho_p = norm_p * np.exp(-((p_arr - p0) ** 2) / (2.0 * (delta_p**2)))
    rho_p_plot = rho_p / np.max(rho_p)

    return UncertaintyResult(
        sigma_x_nm=sigma_x_nm,
        p0_momentum_si=p0,
        state_purity_factor=purity_factor,
        delta_x_m=delta_x,
        delta_x_nm=sigma_x_nm,
        delta_p_si=delta_p,
        uncertainty_product=product,
        hbar_over_two=hbar_2,
        ratio_to_minimum=ratio,
        is_minimum_uncertainty=(abs(ratio - 1.0) < 1e-4),
        x_grid_nm=x_nm.tolist(),
        psi_prob_density_x=rho_x_plot.tolist(),
        psi_real_x=psi_real_plot.tolist(),
        p_grid_scaled=p_grid_scaled.tolist(),
        phi_prob_density_p=rho_p_plot.tolist(),
    )
