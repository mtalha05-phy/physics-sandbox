"""Physics package exports for ScienceQuest Live."""
from app.physics.tunneling import calculate_tunneling, calculate_quantum_transmission, TunnelingResult
from app.physics.double_slit import calculate_double_slit, DoubleSlitResult
from app.physics.uncertainty import calculate_uncertainty, UncertaintyResult
from app.physics.wave_lab import calculate_wave_lab, WaveLabResult
from app.physics.correspondence import calculate_correspondence, CorrespondenceResult

__all__ = [
    "calculate_tunneling",
    "calculate_quantum_transmission",
    "TunnelingResult",
    "calculate_double_slit",
    "DoubleSlitResult",
    "calculate_uncertainty",
    "UncertaintyResult",
    "calculate_wave_lab",
    "WaveLabResult",
    "calculate_correspondence",
    "CorrespondenceResult",
]
