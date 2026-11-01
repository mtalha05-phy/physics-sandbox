"""
Scientific validation tests for Mission 3: The Uncertainty Challenge.
Verifies Delta x * Delta p >= hbar / 2, minimum-uncertainty packets,
and inverse relationship between spatial width and momentum spread.
"""

import pytest
import math
from app.physics.uncertainty import calculate_uncertainty


def test_heisenberg_minimum_uncertainty_gaussian():
    """Unchirped Gaussian wavepacket must strictly saturate Delta x * Delta p = hbar / 2."""
    res = calculate_uncertainty(sigma_x_nm=0.3, packet_chirp=0.0)
    assert res.is_minimum_uncertainty is True
    assert math.isclose(res.ratio_to_minimum, 1.0, rel_tol=1e-4)
    assert math.isclose(res.uncertainty_product, res.hbar_over_two, rel_tol=1e-4)


def test_spatial_narrowing_broadens_momentum():
    """Narrowing spatial packet width sigma_x must strictly broaden momentum spread delta_p."""
    res_wide = calculate_uncertainty(sigma_x_nm=1.0)
    res_narrow = calculate_uncertainty(sigma_x_nm=0.1)

    assert res_narrow.delta_x_nm < res_wide.delta_x_nm
    assert res_narrow.delta_p_si > res_wide.delta_p_si


def test_chirped_state_exceeds_minimum():
    """Chirped or complex state has uncertainty product strictly greater than hbar / 2."""
    res = calculate_uncertainty(sigma_x_nm=0.3, packet_chirp=1.5)
    assert res.ratio_to_minimum > 1.4
    assert res.uncertainty_product > res.hbar_over_two
