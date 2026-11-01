"""
Mission 1: The Impossible Wall - Classical vs Quantum Barrier Transmission.
Provides mathematically validated, numerically stable solutions for 1D rectangular potential barrier.
"""

from dataclasses import dataclass
from typing import Dict, Any, List
import math
import numpy as np

from app.physics.constants import (
    HBAR,
    ELECTRON_MASS,
    ev_to_joules,
    nm_to_meters,
    meters_to_nm,
    PLANCK_H,
)


@dataclass
class TunnelingResult:
    # Inputs in user-facing units
    energy_ev: float
    barrier_height_ev: float
    barrier_width_nm: float
    particle_mass_me: float

    # Classical outcomes
    classical_transmission: float
    classical_reflection: float
    classical_crosses: bool
    classical_note: str

    # Quantum outcomes
    quantum_transmission: float
    quantum_reflection: float
    kappa_or_k2_inv_nm: float
    de_broglie_wavelength_nm: float
    decay_length_nm: float

    # Spatial profile for visualization
    spatial_grid_nm: List[float]
    potential_profile_ev: List[float]
    psi_real: List[float]
    psi_imag: List[float]
    prob_density: List[float]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "energy_ev": round(self.energy_ev, 4),
            "barrier_height_ev": round(self.barrier_height_ev, 4),
            "barrier_width_nm": round(self.barrier_width_nm, 4),
            "particle_mass_me": round(self.particle_mass_me, 4),
            "classical_transmission": self.classical_transmission,
            "classical_reflection": self.classical_reflection,
            "classical_crosses": self.classical_crosses,
            "classical_note": self.classical_note,
            "quantum_transmission": round(self.quantum_transmission, 6),
            "quantum_reflection": round(self.quantum_reflection, 6),
            "kappa_or_k2_inv_nm": round(self.kappa_or_k2_inv_nm, 4),
            "de_broglie_wavelength_nm": round(self.de_broglie_wavelength_nm, 4),
            "decay_length_nm": round(self.decay_length_nm, 4) if self.decay_length_nm < 1e6 else -1.0,
            "spatial_grid_nm": [round(x, 4) for x in self.spatial_grid_nm],
            "potential_profile_ev": [round(v, 4) for v in self.potential_profile_ev],
            "psi_real": [round(p, 5) for p in self.psi_real],
            "psi_imag": [round(p, 5) for p in self.psi_imag],
            "prob_density": [round(p, 5) for p in self.prob_density],
        }


def calculate_quantum_transmission(
    energy_j: float,
    v0_j: float,
    width_m: float,
    mass_kg: float,
) -> float:
    """
    Compute transmission coefficient T through a rectangular barrier.
    Handles E < V0, E = V0, and E > V0 with numerical stability guarantees.
    """
    if energy_j <= 0:
        return 0.0

    # Boundary: E == V0 (or within relative tolerance 1e-12)
    rel_diff = abs(energy_j - v0_j) / max(energy_j, v0_j)
    if rel_diff < 1e-9:
        denom = 1.0 + (mass_kg * (width_m**2) * v0_j) / (2.0 * (HBAR**2))
        return 1.0 / denom

    if energy_j < v0_j:
        # Tunneling regime (E < V0)
        # kappa = sqrt(2m(V0 - E)) / hbar
        delta = v0_j - energy_j
        kappa = math.sqrt(2.0 * mass_kg * delta) / HBAR
        ka = kappa * width_m

        # Numerical stability handling for large ka
        if ka > 50.0:
            # When ka > 50, sinh(ka) ~ 0.5 * exp(ka)
            # sinh^2(ka) ~ 0.25 * exp(2ka)
            # T ~ 1 / [ (V0^2 * exp(2ka)) / (16 * E * (V0 - E)) ]
            # = (16 * E * (V0 - E) / V0^2) * exp(-2ka)
            if 2.0 * ka > 700.0:
                return 0.0
            factor = (16.0 * energy_j * delta) / (v0_j**2)
            return factor * math.exp(-2.0 * ka)

        sinh_ka = math.sinh(ka)
        denom_add = (v0_j**2 * (sinh_ka**2)) / (4.0 * energy_j * delta)
        return 1.0 / (1.0 + denom_add)
    else:
        # Over-barrier regime (E > V0)
        # k2 = sqrt(2m(E - V0)) / hbar
        excess = energy_j - v0_j
        k2 = math.sqrt(2.0 * mass_kg * excess) / HBAR
        k2a = k2 * width_m

        sin_k2a = math.sin(k2a)
        denom_add = (v0_j**2 * (sin_k2a**2)) / (4.0 * energy_j * excess)
        return 1.0 / (1.0 + denom_add)


def calculate_tunneling(
    energy_ev: float = 3.5,
    barrier_height_ev: float = 5.0,
    barrier_width_nm: float = 0.5,
    particle_mass_me: float = 1.0,
    num_grid_points: int = 250,
) -> TunnelingResult:
    """
    Full physical simulation of classical and quantum rectangular barrier interaction.
    """
    for _name, _val in (('energy_ev', energy_ev), ('barrier_height_ev', barrier_height_ev),
                        ('barrier_width_nm', barrier_width_nm), ('particle_mass_me', particle_mass_me)):
        if not math.isfinite(float(_val)):
            raise ValueError(f'{_name} must be finite')
    # Guard against invalid negative or zero parameters
    energy_ev = max(0.01, float(energy_ev))
    barrier_height_ev = max(0.01, float(barrier_height_ev))
    barrier_width_nm = max(0.01, float(barrier_width_nm))
    particle_mass_me = max(0.01, float(particle_mass_me))

    # Convert to SI units
    energy_j = ev_to_joules(energy_ev)
    v0_j = ev_to_joules(barrier_height_ev)
    width_m = nm_to_meters(barrier_width_nm)
    mass_kg = particle_mass_me * ELECTRON_MASS

    # 1. Classical Model
    if energy_j < v0_j:
        classical_trans = 0.0
        classical_ref = 1.0
        classical_cross = False
        classical_note = (
            f"Particle energy ({energy_ev:.2f} eV) is less than barrier height ({barrier_height_ev:.2f} eV). "
            f"In classical mechanics, kinetic energy K = E - V < 0 is impossible, so transmission is strictly 0%."
        )
    elif abs(energy_j - v0_j) / max(energy_j, v0_j) < 1e-9:
        classical_trans = 0.0
        classical_ref = 1.0
        classical_cross = False
        classical_note = (
            f"Particle energy matches barrier height exactly. The classical particle decelerates to v=0 "
            f"at the boundary and cannot cross."
        )
    else:
        classical_trans = 1.0
        classical_ref = 0.0
        classical_cross = True
        classical_note = (
            f"Particle energy ({energy_ev:.2f} eV) exceeds barrier height ({barrier_height_ev:.2f} eV). "
            f"The classical particle passes over the barrier with reduced speed v = sqrt(2(E-V0)/m)."
        )

    # 2. Quantum Model
    q_trans = calculate_quantum_transmission(energy_j, v0_j, width_m, mass_kg)
    q_trans = max(0.0, min(1.0, q_trans))
    q_ref = 1.0 - q_trans

    # Characteristic scales
    # Incident momentum and de Broglie wavelength
    p_incident = math.sqrt(2.0 * mass_kg * energy_j)
    de_broglie_m = PLANCK_H / p_incident
    de_broglie_nm = meters_to_nm(de_broglie_m)

    k1 = p_incident / HBAR

    if energy_j < v0_j:
        kappa = math.sqrt(2.0 * mass_kg * (v0_j - energy_j)) / HBAR
        decay_m = 1.0 / kappa if kappa > 0 else float("inf")
        decay_nm = meters_to_nm(decay_m)
        kappa_nm = kappa * 1e-9
    else:
        decay_nm = float("inf")
        k2 = math.sqrt(2.0 * mass_kg * (energy_j - v0_j)) / HBAR
        kappa_nm = k2 * 1e-9

    # 3. Wavefunction Spatial Profile on grid [-x_left, a + x_right]
    x_left_nm = max(1.5 * de_broglie_nm, 1.5 * barrier_width_nm, 1.0)
    x_right_nm = max(1.5 * de_broglie_nm, 1.5 * barrier_width_nm, 1.0)
    total_length_nm = x_left_nm + barrier_width_nm + x_right_nm

    x_grid_nm = np.linspace(-x_left_nm, barrier_width_nm + x_right_nm, num_grid_points)
    x_grid_m = x_grid_nm * 1e-9

    # Solve matching conditions for stationary 1D scattering state:
    # Region 1 (x < 0):      psi(x) = exp(i*k1*x) + r * exp(-i*k1*x)
    # Region 2 (0 <= x <= a):
    #   Sub-barrier (E < V0): psi(x) = A * exp(-kappa*x) + B * exp(kappa*x)
    #   Over-barrier (E > V0): psi(x) = A * exp(i*k2*x) + B * exp(-i*k2*x)
    # Region 3 (x > a):      psi(x) = t * exp(i*k1*(x - width_m))
    # Boundary equations at x = 0:
    #   1 + r = A + B
    #   i*k1*(1 - r) = psi_2'(0)
    # Boundary equations at x = a:
    #   psi_2(a) = t
    #   psi_2'(a) = i*k1*t

    k1_c = complex(k1, 0.0)

    near_threshold = abs(energy_j - v0_j) <= 1e-9 * v0_j
    if near_threshold:
        # E == V0: k2 = 0, so inside the barrier psi = A + B x (linear). Matching psi and psi' at
        # x = 0 and x = a gives r = -i k1 a / (2 - i k1 a) and t = 1 - r = 2 / (2 - i k1 a),
        # hence |t|^2 = 1 / (1 + k1^2 a^2 / 4), the same E = V0 limit as the closed-form transmission.
        # (A generic 4x4 solve is singular here.)
        t_coeff = 2.0 / (2.0 - 1j * k1 * width_m)
        r_coeff = 1.0 - t_coeff
        A_lin = 1.0 + r_coeff
        B_lin = 1j * k1 * t_coeff

        def eval_psi(xm: float) -> complex:
            if xm < 0.0:
                return np.exp(1j * k1 * xm) + r_coeff * np.exp(-1j * k1 * xm)
            elif xm <= width_m:
                return A_lin + B_lin * xm
            else:
                return t_coeff * np.exp(1j * k1 * (xm - width_m))

    elif energy_j < v0_j:
        kappa_c = complex(kappa, 0.0)
        # Matrix for [r, A, B, t]
        # Eq 1: r - A - B = -1
        # Eq 2: -i*k1*r + kappa*A - kappa*B = -i*k1
        # Eq 3: exp(-kappa*a)*A + exp(kappa*a)*B - t = 0
        # Eq 4: -kappa*exp(-kappa*a)*A + kappa*exp(kappa*a)*B - i*k1*t = 0
        # To avoid exponential overflow when kappa*a is large, factor out exp(kappa*a):
        # Let B_tilde = B * exp(kappa*a)
        # Then Eq 3: exp(-kappa*a)*A + B_tilde - t = 0
        # Eq 4: -kappa*exp(-kappa*a)*A + kappa*B_tilde - i*k1*t = 0
        # Eq 1: r - A - exp(-kappa*a)*B_tilde = -1
        # Eq 2: -i*k1*r + kappa*A - kappa*exp(-kappa*a)*B_tilde = -i*k1
        ka = kappa * width_m
        if ka > 100.0:
            # Deep tunneling: A dominates at 0, transmitted wave t is very small
            exp_neg = 0.0
        else:
            exp_neg = math.exp(-ka)

        M = np.array([
            [1.0 + 0j, -1.0 + 0j, -exp_neg + 0j, 0.0 + 0j],
            [-1j * k1_c, kappa_c, -kappa_c * exp_neg, 0.0 + 0j],
            [0.0 + 0j, exp_neg + 0j, 1.0 + 0j, -1.0 + 0j],
            [0.0 + 0j, -kappa_c * exp_neg, kappa_c, -1j * k1_c],
        ], dtype=np.complex128)

        Y = np.array([-1.0 + 0j, -1j * k1_c, 0.0 + 0j, 0.0 + 0j], dtype=np.complex128)
        sol = np.linalg.solve(M, Y)
        r_coeff = sol[0]
        A_coeff = sol[1]
        B_tilde = sol[2]
        t_coeff = sol[3]

        def eval_psi(xm: float) -> complex:
            if xm < 0.0:
                return np.exp(1j * k1 * xm) + r_coeff * np.exp(-1j * k1 * xm)
            elif xm <= width_m:
                term1 = A_coeff * np.exp(-kappa * xm)
                # B * exp(kappa*xm) = B_tilde * exp(kappa*(xm - width_m))
                term2 = B_tilde * np.exp(kappa * (xm - width_m))
                return term1 + term2
            else:
                return t_coeff * np.exp(1j * k1 * (xm - width_m))

    else:
        k2 = math.sqrt(2.0 * mass_kg * (energy_j - v0_j)) / HBAR  # energy_j > v0_j is guaranteed by the branch
        k2_c = complex(k2, 0.0)
        # Eq 1: r - A - B = -1
        # Eq 2: -i*k1*r - i*k2*A + i*k2*B = -i*k1
        # Eq 3: exp(i*k2*a)*A + exp(-i*k2*a)*B - t = 0
        # Eq 4: i*k2*exp(i*k2*a)*A - i*k2*exp(-i*k2*a)*B - i*k1*t = 0
        e_pos = np.exp(1j * k2 * width_m)
        e_neg = np.exp(-1j * k2 * width_m)

        M = np.array([
            [1.0 + 0j, -1.0 + 0j, -1.0 + 0j, 0.0 + 0j],
            [-1j * k1_c, -1j * k2_c, 1j * k2_c, 0.0 + 0j],
            [0.0 + 0j, e_pos, e_neg, -1.0 + 0j],
            [0.0 + 0j, 1j * k2_c * e_pos, -1j * k2_c * e_neg, -1j * k1_c],
        ], dtype=np.complex128)

        Y = np.array([-1.0 + 0j, -1j * k1_c, 0.0 + 0j, 0.0 + 0j], dtype=np.complex128)
        sol = np.linalg.solve(M, Y)
        r_coeff = sol[0]
        A_coeff = sol[1]
        B_coeff = sol[2]
        t_coeff = sol[3]

        def eval_psi(xm: float) -> complex:
            if xm < 0.0:
                return np.exp(1j * k1 * xm) + r_coeff * np.exp(-1j * k1 * xm)
            elif xm <= width_m:
                return A_coeff * np.exp(1j * k2 * xm) + B_coeff * np.exp(-1j * k2 * xm)
            else:
                return t_coeff * np.exp(1j * k1 * (xm - width_m))

    # Evaluate along grid
    psi_vals = np.array([eval_psi(xm) for xm in x_grid_m])
    v_profile = np.array([barrier_height_ev if (0.0 <= x <= barrier_width_nm) else 0.0 for x in x_grid_nm])

    psi_real = np.real(psi_vals)
    psi_imag = np.imag(psi_vals)
    prob_dens = np.abs(psi_vals) ** 2

    return TunnelingResult(
        energy_ev=energy_ev,
        barrier_height_ev=barrier_height_ev,
        barrier_width_nm=barrier_width_nm,
        particle_mass_me=particle_mass_me,
        classical_transmission=classical_trans,
        classical_reflection=classical_ref,
        classical_crosses=classical_cross,
        classical_note=classical_note,
        quantum_transmission=q_trans,
        quantum_reflection=q_ref,
        kappa_or_k2_inv_nm=kappa_nm,
        de_broglie_wavelength_nm=de_broglie_nm,
        decay_length_nm=decay_nm,
        spatial_grid_nm=x_grid_nm.tolist(),
        potential_profile_ev=v_profile.tolist(),
        psi_real=psi_real.tolist(),
        psi_imag=psi_imag.tolist(),
        prob_density=prob_dens.tolist(),
    )
