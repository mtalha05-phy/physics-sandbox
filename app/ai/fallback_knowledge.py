"""
Curated scientific knowledge and fallback explanations for Quark AI Companion.
Ensures Quark can always provide rigorous, multi-tiered explanations even when offline.
"""

from typing import Dict, Any

EXPERIMENT_EXPLANATIONS = {
    "mission_1": {
        "title": "Quantum Tunneling vs Classical Barrier",
        "explorer": (
            "Beep boop! Imagine rolling a skateboard toward a steep ramp. If you don't kick hard enough, "
            "you roll back down every time—that's classical physics! But in the quantum world, particles like electrons "
            "are also fuzzy probability waves. Part of that wave can leak right through the wall and appear on the other side! "
            "That's quantum tunneling!"
        ),
        "scientist": (
            "In classical mechanics, a particle inside a barrier would need negative kinetic energy K = E - V0 < 0, "
            "which is physically impossible (momentum would be imaginary). In quantum mechanics, the Schrödinger equation "
            "has an exponentially decaying evanescent solution inside the barrier: psi(x) ~ exp(-kappa * x). "
            "Because the barrier has finite width 'a', the wave amplitude does not drop to zero, yielding a finite transmission "
            "probability T = 1 / [1 + V0^2 sinh^2(kappa*a) / (4E(V0 - E))]."
        ),
        "researcher": (
            "We solve the 1D time-independent Schrödinger equation (-hbar^2/(2m) d^2/dx^2 + V(x))psi = E psi. "
            "For E < V0, the wavevector k1 = sqrt(2mE)/hbar in Regions I & III matches the decay parameter kappa = sqrt(2m(V0 - E))/hbar "
            "in Region II. Imposing C1 continuity of psi and dpsi/dx at x=0 and x=a yields transmission coefficient T. "
            "Notice that increasing barrier thickness 'a' exponentially suppresses T, while increasing particle mass 'm' increases kappa, "
            "illustrating why macroscopic objects with vast mass have virtually zero tunneling probability."
        ),
    },
    "mission_2": {
        "title": "Double-Slit Wave-Particle Duality",
        "explorer": (
            "Waves in water make ripples that crisscross into bright and dark stripes! When electrons go through two slits, "
            "they create that exact same striped pattern on the screen—showing they behave like waves. But if we put a detector "
            "at the slits to spy on which door each electron uses, the stripes vanish into one plain, smooth blob! Looking destroyed the wave dance!"
        ),
        "scientist": (
            "The double-slit experiment demonstrates that quantum states evolve as coherent superpositions of probability amplitudes: "
            "psi_total = psi_1 + psi_2. The detected intensity is the squared magnitude P(y) = |psi_1 + psi_2|^2 = |psi_1|^2 + |psi_2|^2 + 2 Re(psi_1* psi_2). "
            "When which-path measurement is introduced, the quantum system becomes entangled with the detector states, causing environmental decoherence. "
            "The interference cross-term vanishes, leaving an incoherent sum: P_measured(y) = |psi_1|^2 + |psi_2|^2."
        ),
        "researcher": (
            "Formally, in the density matrix formalism rho, the off-diagonal coherence terms rho_12 and rho_21 vanish upon tracing over "
            "orthogonal detector pointer states <d1|d2> = 0. Notice this does not require human consciousness; any irreversible physical "
            "entanglement that encodes distinguishable which-path information destroys the phase relationship necessary for coherent interference."
        ),
    },
    "mission_3": {
        "title": "Heisenberg's Uncertainty Principle",
        "explorer": (
            "If you want to know exactly where a particle is, you have to squeeze it tight. But the more you squeeze it, "
            "the wilder its speed gets! You can't pin down both where it is AND where it's going at the exact same moment. "
            "It's not our microscopes being blurry—it's a fundamental rule of the universe!"
        ),
        "scientist": (
            "Heisenberg's Uncertainty Principle states that position x and momentum p are Fourier conjugate variables: Delta x * Delta p >= hbar / 2. "
            "A spatially localized state requires a broad superposition of spatial frequencies (plane waves e^(i k x)), "
            "which corresponds to a wide spread of momentum eigenstates via de Broglie's relation p = hbar * k. "
            "A minimum-uncertainty Gaussian wavepacket saturates the inequality at exactly hbar / 2."
        ),
        "researcher": (
            "Mathematically, this derives from the Robertson-Schrödinger relation for non-commuting self-adjoint operators [x_hat, p_hat] = i * hbar. "
            "The variance inequality (Delta A)^2 (Delta B)^2 >= (1/4) |<[A, B]>|^2 yields Delta x * Delta p >= hbar / 2. "
            "This shows the bound follows from the Fourier structure of non-commuting observables, not from clumsy measurement disturbance."
        ),
    },
    "mission_4": {
        "title": "The Wave Laboratory",
        "explorer": (
            "When two waves meet crest-to-crest, they combine into a giant mega-wave! But when a crest meets a trough, they cancel each other out "
            "into flat water! Both sound waves, water waves, light waves, and quantum probability waves follow this beautiful rule."
        ),
        "scientist": (
            "Classical waves follow linear wave equations where superposition holds: y_net(x,t) = y1(x,t) + y2(x,t). "
            "For two waves with phase difference delta, resultant amplitude is A_res = sqrt(A1^2 + A2^2 + 2 A1 A2 cos(delta)). "
            "When delta = 0, constructive interference yields maximum intensity. When delta = pi, destructive interference yields zero amplitude. "
            "In quantum mechanics, probability amplitudes interfere linearly before being squared to obtain observable detection statistics."
        ),
        "researcher": (
            "While both systems exhibit constructive and destructive interference mathematically, the physical ontology differs fundamentally: "
            "Classical intensity represents real energy flux distributed continuously in space. In quantum mechanics, psi(x) is an abstract probability amplitude, "
            "and detection always occurs as discrete localized energy quanta (e.g. single electron clicks on a CCD), with probability density governed by Born's rule."
        ),
    },
    "mission_5": {
        "title": "The Classical–Quantum Boundary",
        "explorer": (
            "Why doesn't a thrown baseball turn into a wave and tunnel through a catcher's mitt? Because the baseball is huge! "
            "Its quantum wave spreads so slowly that it would take far longer than the age of the universe to notice. For big objects, quantum rules blend so smoothly into "
            "Newton's laws that classical physics works like magic!"
        ),
        "scientist": (
            "The Correspondence Principle (Bohr, Ehrenfest) demonstrates that quantum expectation values follow classical equations of motion: "
            "d<x>/dt = <p>/m and d<p>/dt = -<dV/dx>. For a macroscopic mass m, the wavepacket spreading timescale tau = 2 m sigma_0^2 / hbar "
            "is many orders of magnitude larger than the age of the universe. Furthermore, environmental decoherence from cosmic background and air molecules "
            "suppresses the off-diagonal terms of the density matrix on timescales far shorter than any experiment can resolve, eliminating visible macroscopic interference."
        ),
        "researcher": (
            "The classical world is not an ontological regime separate from quantum mechanics; rather, classical dynamics emerges as an effective field theory "
            "in the semiclassical limit where the action S >> hbar. Through continuous monitoring by the environment (decoherence program, Zurek), "
            "pointer states resembling localized coherent wavepackets are dynamically selected, explaining why classical phase-space trajectories are observed."
        ),
    },
}


def get_curated_explanation(mission_id: str, level: str) -> str:
    level_key = level.lower().strip()
    if level_key not in ("explorer", "scientist", "researcher"):
        level_key = "scientist"
    m_data = EXPERIMENT_EXPLANATIONS.get(mission_id, EXPERIMENT_EXPLANATIONS["mission_1"])
    return m_data.get(level_key, m_data["scientist"])
