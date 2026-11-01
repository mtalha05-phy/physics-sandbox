"""
Scientific validation tests for Mission 1: The Impossible Wall.
Tests verify physical accuracy, boundary behaviors, limits, and numerical stability.
"""

import pytest
import math
from app.physics.tunneling import calculate_tunneling, calculate_quantum_transmission
from app.physics.constants import ev_to_joules, nm_to_meters, ELECTRON_MASS


def test_classical_barrier_reflection_below_barrier():
    """When E < V0, classical transmission must be strictly zero."""
    res = calculate_tunneling(energy_ev=3.0, barrier_height_ev=6.0, barrier_width_nm=0.5)
    assert res.classical_transmission == 0.0
    assert res.classical_reflection == 1.0
    assert res.classical_crosses is False


def test_classical_barrier_transmission_above_barrier():
    """When E > V0, classical particle must cross with transmission 1.0."""
    res = calculate_tunneling(energy_ev=8.0, barrier_height_ev=5.0, barrier_width_nm=0.5)
    assert res.classical_transmission == 1.0
    assert res.classical_reflection == 0.0
    assert res.classical_crosses is True


def test_classical_barrier_exact_threshold():
    """When E == V0, particle reaches boundary with zero kinetic energy and cannot cross."""
    res = calculate_tunneling(energy_ev=5.0, barrier_height_ev=5.0, barrier_width_nm=0.5)
    assert res.classical_transmission == 0.0
    assert res.classical_crosses is False


def test_quantum_tunneling_nonzero_below_barrier():
    """Quantum particle with E < V0 must have non-zero transmission probability."""
    res = calculate_tunneling(energy_ev=3.5, barrier_height_ev=5.0, barrier_width_nm=0.4)
    assert res.quantum_transmission > 0.0
    assert res.quantum_transmission < 1.0
    # Conservation of probability
    assert math.isclose(res.quantum_transmission + res.quantum_reflection, 1.0, rel_tol=1e-5)


def test_quantum_tunneling_width_dependence():
    """For sub-barrier tunneling, increasing barrier width strictly decreases transmission."""
    res_thin = calculate_tunneling(energy_ev=4.0, barrier_height_ev=6.0, barrier_width_nm=0.2)
    res_med = calculate_tunneling(energy_ev=4.0, barrier_height_ev=6.0, barrier_width_nm=0.5)
    res_thick = calculate_tunneling(energy_ev=4.0, barrier_height_ev=6.0, barrier_width_nm=1.0)

    assert res_thin.quantum_transmission > res_med.quantum_transmission
    assert res_med.quantum_transmission > res_thick.quantum_transmission


def test_quantum_tunneling_barrier_height_dependence():
    """Increasing barrier height V0 for fixed sub-barrier E decreases transmission."""
    res_low = calculate_tunneling(energy_ev=4.0, barrier_height_ev=5.0, barrier_width_nm=0.5)
    res_high = calculate_tunneling(energy_ev=4.0, barrier_height_ev=8.0, barrier_width_nm=0.5)

    assert res_low.quantum_transmission > res_high.quantum_transmission


def test_quantum_tunneling_energy_dependence():
    """Increasing particle energy E toward V0 increases transmission."""
    res_low_e = calculate_tunneling(energy_ev=2.0, barrier_height_ev=6.0, barrier_width_nm=0.5)
    res_high_e = calculate_tunneling(energy_ev=5.5, barrier_height_ev=6.0, barrier_width_nm=0.5)

    assert res_high_e.quantum_transmission > res_low_e.quantum_transmission


def test_quantum_thin_barrier_limit():
    """As barrier width approaches 0, transmission must approach 1.0."""
    res = calculate_tunneling(energy_ev=3.0, barrier_height_ev=6.0, barrier_width_nm=0.001)
    assert res.quantum_transmission > 0.99


def test_numerical_stability_large_barrier():
    """Extreme barrier width must not overflow floats or crash with sinh overflow."""
    res = calculate_tunneling(energy_ev=1.0, barrier_height_ev=20.0, barrier_width_nm=50.0)
    assert 0.0 <= res.quantum_transmission <= 1e-12
    assert math.isclose(res.quantum_reflection, 1.0, rel_tol=1e-6)


def test_quantum_overbarrier_transmission_resonances():
    """For E > V0, transmission should reach peaks (resonance) when k2 * a is integer multiple of pi."""
    res = calculate_tunneling(energy_ev=7.0, barrier_height_ev=4.0, barrier_width_nm=0.5)
    assert res.quantum_transmission > 0.5
    assert res.quantum_transmission <= 1.0
    assert math.isclose(res.quantum_transmission + res.quantum_reflection, 1.0, rel_tol=1e-5)


def test_continuity_across_threshold():
    """Transmission should behave continuously across the E = V0 threshold."""
    v0 = 5.0
    res_below = calculate_tunneling(energy_ev=v0 - 1e-4, barrier_height_ev=v0, barrier_width_nm=0.5)
    res_at = calculate_tunneling(energy_ev=v0, barrier_height_ev=v0, barrier_width_nm=0.5)
    res_above = calculate_tunneling(energy_ev=v0 + 1e-4, barrier_height_ev=v0, barrier_width_nm=0.5)

    assert math.isclose(res_below.quantum_transmission, res_at.quantum_transmission, rel_tol=1e-2)
    assert math.isclose(res_above.quantum_transmission, res_at.quantum_transmission, rel_tol=1e-2)


def test_wavefunction_grid_output():
    """Spatial grid arrays must be properly populated and of consistent length."""
    res = calculate_tunneling(energy_ev=3.5, barrier_height_ev=5.0, barrier_width_nm=0.5, num_grid_points=100)
    assert len(res.spatial_grid_nm) == 100
    assert len(res.potential_profile_ev) == 100
    assert len(res.psi_real) == 100
    assert len(res.psi_imag) == 100
    assert len(res.prob_density) == 100
    # Prob density must be non-negative everywhere
    assert all(p >= 0.0 for p in res.prob_density)
