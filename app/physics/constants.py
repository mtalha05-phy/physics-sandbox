"""
Physical constants and unit conversion utilities for ScienceQuest Live.
All calculations use SI units internally for absolute consistency.
"""

# Fundamental Physical Constants (CODATA 2018 / SI Standard)
HBAR: float = 1.054571817e-34       # Reduced Planck constant (J*s)
PLANCK_H: float = 6.62607015e-34    # Planck constant (J*s)
ELECTRON_MASS: float = 9.1093837e-31 # Electron rest mass (kg)
EV_TO_JOULE: float = 1.602176634e-19 # 1 electronvolt in Joules
NM_TO_METER: float = 1.0e-9         # 1 nanometer in meters
ANGSTROM_TO_METER: float = 1.0e-10  # 1 Angstrom in meters
SPEED_OF_LIGHT: float = 299792458.0 # Speed of light in vacuum (m/s)

def ev_to_joules(energy_ev: float) -> float:
    """Convert energy from electronvolts (eV) to Joules (J)."""
    return float(energy_ev) * EV_TO_JOULE

def joules_to_ev(energy_j: float) -> float:
    """Convert energy from Joules (J) to electronvolts (eV)."""
    return float(energy_j) / EV_TO_JOULE

def nm_to_meters(length_nm: float) -> float:
    """Convert length from nanometers (nm) to meters (m)."""
    return float(length_nm) * NM_TO_METER

def meters_to_nm(length_m: float) -> float:
    """Convert length from meters (m) to nanometers (nm)."""
    return float(length_m) / NM_TO_METER
