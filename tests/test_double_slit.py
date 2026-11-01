"""
Scientific validation tests for Mission 2: Double-Slit Experiment.
Verifies interference, single-slit diffraction, and which-path decoherence.
"""

import pytest
import math
from app.physics.double_slit import calculate_double_slit


def test_two_slit_interference_has_fringes():
    """Two coherent slits must produce multiple interference fringes."""
    res = calculate_double_slit(num_slits=2, which_path_enabled=False)
    assert res.fringes_peak_count >= 3
    assert res.visibility > 0.9


def test_which_path_destroys_interference():
    """Which-path measurement destroys coherent interference fringes (visibility drops to 0)."""
    res_coherent = calculate_double_slit(num_slits=2, which_path_enabled=False)
    res_measured = calculate_double_slit(num_slits=2, which_path_enabled=True)

    # Incoherent pattern has smooth sum without high-frequency interference ripples
    assert res_measured.visibility == 0.0
    assert res_measured.fringes_peak_count < res_coherent.fringes_peak_count


def test_single_slit_no_interference_ripples():
    """Single slit produces pure single-slit diffraction with no double-slit fringes."""
    res = calculate_double_slit(num_slits=1, which_path_enabled=False)
    assert res.visibility == 0.0
