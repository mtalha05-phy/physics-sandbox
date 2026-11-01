"""
Independent physics validation.

These tests do NOT re-use the formulas under test. They compare against a different method
(a brute-force 4x4 matching solve, FFT moments, flux conservation, closed-form limits). Each one
guards a bug that earlier versions of the code really had.
"""

import itertools
import math

import numpy as np

from app.physics.constants import ELECTRON_MASS, EV_TO_JOULE, HBAR
from app.physics.correspondence import calculate_correspondence
from app.physics.double_slit import calculate_double_slit
from app.physics.tunneling import calculate_quantum_transmission, calculate_tunneling
from app.physics.uncertainty import calculate_uncertainty


def _transfer_matrix_T(e_ev, v_ev, a_nm, m_me):
    """Reference transmission from a direct solve of the three-region matching conditions."""
    E, V, a, m = e_ev * EV_TO_JOULE, v_ev * EV_TO_JOULE, a_nm * 1e-9, m_me * ELECTRON_MASS
    k1 = math.sqrt(2 * m * E) / HBAR
    k2 = np.sqrt(complex(2 * m * (E - V))) / HBAR
    M = np.array([[1, -1, -1, 0], [-1j * k1, -1j * k2, 1j * k2, 0],
                  [0, np.exp(1j * k2 * a), np.exp(-1j * k2 * a), -1],
                  [0, 1j * k2 * np.exp(1j * k2 * a), -1j * k2 * np.exp(-1j * k2 * a), -1j * k1]], dtype=complex)
    return abs(np.linalg.solve(M, np.array([-1, -1j * k1, 0, 0], dtype=complex))[3]) ** 2


def test_transmission_matches_independent_solver():
    checked = 0
    for e, v, a, m in itertools.product([0.5, 1, 3.5, 4.9, 5.1, 8, 10], [1, 5, 12], [0.1, 0.45, 1.0, 2.0], [0.5, 1, 5]):
        if abs(e - v) < 1e-6:
            continue
        ref = _transfer_matrix_T(e, v, a, m)
        if ref < 1e-12:  # below this the reference itself loses precision
            continue
        got = calculate_quantum_transmission(e * EV_TO_JOULE, v * EV_TO_JOULE, a * 1e-9, m * ELECTRON_MASS)
        assert abs(got - ref) / ref < 1e-9, (e, v, a, m, got, ref)
        checked += 1
    assert checked > 100


def test_wavefunction_conserves_flux_under_and_over_barrier():
    """|psi|^2 on the right must equal T and the left fringes must follow |r|^2 = 1 - T.

    Regression: for E > V0 the over-barrier wavevector used a floor of 6.24 eV, so the plotted wave
    showed (almost) full transmission while the reported T was 0.64."""
    for e, v, a, m in [(3.5, 5, 0.45, 1), (6, 5, 0.45, 1), (2, 8, 1.0, 2), (9.9, 10, 0.3, 1), (10, 1, 2, 5)]:
        r = calculate_tunneling(e, v, a, m, num_grid_points=2000)
        x, rho, T = np.array(r.spatial_grid_nm), np.array(r.prob_density), r.quantum_transmission
        assert abs(rho[x > a + 1e-9].mean() - T) < 2e-3 * max(1.0, T), (e, v)
        left, rr = rho[x < -1e-9], math.sqrt(1 - T)
        assert abs(left.max() - (1 + rr) ** 2) < 0.02
        assert abs(left.min() - (1 - rr) ** 2) < 0.02


def test_exact_threshold_energy_is_handled():
    """E == V0 makes k2 = 0 (singular matching matrix); it must still give the closed-form limit."""
    r = calculate_tunneling(5.0, 5.0, 0.45, 1.0, num_grid_points=500)
    k1 = math.sqrt(2 * ELECTRON_MASS * 5.0 * EV_TO_JOULE) / HBAR
    expected = 1.0 / (1.0 + (k1 * 0.45e-9) ** 2 / 4.0)
    assert abs(r.quantum_transmission - expected) < 1e-9
    x, rho = np.array(r.spatial_grid_nm), np.array(r.prob_density)
    assert abs(rho[x > 0.45 + 1e-9].mean() - expected) < 1e-3


def test_decay_constant_is_exported():
    """The UI shows kappa; it used to be missing from the payload and always displayed 0."""
    d = calculate_tunneling(3.5, 5.0, 0.45, 1.0).to_dict()
    kappa = math.sqrt(2 * ELECTRON_MASS * 1.5 * EV_TO_JOULE) / HBAR * 1e-9
    assert abs(d["kappa_or_k2_inv_nm"] - kappa) < 1e-3


def _numeric_uncertainty_ratio(sigma_nm, chirp):
    sx = sigma_nm * 1e-9
    n = 2 ** 16
    x = np.linspace(-30 * sx, 30 * sx, n, endpoint=False)
    dx = x[1] - x[0]
    psi = np.exp(-x ** 2 / (4 * sx ** 2) + 1j * (chirp / (4 * sx ** 2)) * x ** 2)  # phase used by the code
    psi /= np.sqrt(np.sum(abs(psi) ** 2) * dx)
    rho = abs(psi) ** 2
    Dx = math.sqrt(np.sum((x - np.sum(x * rho) * dx) ** 2 * rho) * dx)
    k = np.fft.fftshift(np.fft.fftfreq(n, dx)) * 2 * np.pi
    prho = abs(np.fft.fftshift(np.fft.fft(psi))) ** 2
    prho /= prho.sum()
    Dp = HBAR * math.sqrt(np.sum((k - np.sum(k * prho)) ** 2 * prho))
    return Dx * Dp / (HBAR / 2)


def test_uncertainty_product_matches_fft_moments():
    """Regression: chirp used b = C/(2 sigma^2) in the phase but sqrt(1+C^2) for dp (true value sqrt(1+4C^2))."""
    for chirp in [0.0, 0.5, 1.0, 3.0]:
        reported = calculate_uncertainty(sigma_x_nm=0.25, central_energy_ev=5.0, packet_chirp=chirp).ratio_to_minimum
        assert abs(reported - _numeric_uncertainty_ratio(0.25, chirp)) < 5e-3, chirp


def test_uncertainty_never_below_heisenberg_bound():
    for sigma, chirp in itertools.product([0.05, 0.25, 1.5], [0.0, 1.0, 3.0]):
        r = calculate_uncertainty(sigma_x_nm=sigma, central_energy_ev=5.0, packet_chirp=chirp)
        assert r.uncertainty_product >= r.hbar_over_two * (1 - 1e-9)


def test_double_slit_fringe_spacing_and_visibility():
    r = calculate_double_slit(0.5, 2.5, 0.5, 1.2, False, 2, num_points=4001)
    assert abs(r.fringe_spacing_mm - 0.5e-9 * 1.2 / 2.5e-6 * 1e3) < 1e-9
    y, p = np.array(r.screen_positions_mm), np.array(r.quantum_probability)
    peaks = [y[i] for i in range(1, len(p) - 1) if p[i] > p[i - 1] and p[i] >= p[i + 1] and p[i] > 0.05]
    centre = sorted(peaks, key=abs)[:5]   # the sloping envelope pulls outer maxima slightly inward
    assert abs(np.mean(np.diff(sorted(centre))) - r.fringe_spacing_mm) < 0.005
    assert r.fringes_peak_count == len(peaks)    # analytic count agrees with the numerical one
    assert r.visibility == 1.0 and r.fringes_peak_count >= 3


def test_which_path_follows_englert_greenberger():
    for strength in [0.0, 0.3, 0.6, 1.0]:
        r = calculate_double_slit(which_path_enabled=True, which_path_strength=strength)
        assert abs(r.visibility - math.sqrt(1 - strength ** 2)) < 1e-12
    full = calculate_double_slit(which_path_enabled=True, which_path_strength=1.0)
    single = calculate_double_slit(num_slits=1)
    assert np.allclose(full.quantum_probability, single.quantum_probability, atol=1e-6)  # incoherent sum
    assert full.fringes_peak_count == 0


def test_classical_particles_differ_from_quantum_interference():
    r = calculate_double_slit()
    assert not np.allclose(r.quantum_probability, r.classical_particle_pattern, atol=0.05)


def test_correspondence_numbers_and_output_precision():
    ball = calculate_correspondence("baseball", 10.0, 1.0)
    years = ball.dispersion_timescale_s / 3.156e7
    assert 1e19 < years < 1e21                       # ~1e20 years, NOT "millions of years"
    assert years > 1.4e10                            # far beyond the age of the universe
    electron = calculate_correspondence("electron", 10.0, 1e-14).to_dict()
    assert any(v > 0 for v in electron["quantum_upper_bound_m"])   # used to round to 0.0 everywhere
    assert electron["quantum_upper_bound_m"][-1] > electron["quantum_lower_bound_m"][-1]
