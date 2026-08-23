"""
orbital_invariant_validator.py
Dijkstra-inspired invariant checker for orbital mechanics.
Each propagation step must preserve physical laws as loop invariants.
"""

from typing import Tuple, Optional
from dataclasses import dataclass
from math import sqrt

@dataclass
class OrbitalState:
    """State vector with immutable invariants."""
    position: Tuple[float, float, float]  # km
    velocity: Tuple[float, float, float]  # km/s
    epoch: float  # Julian date
    
    def __post_init__(self):
        """Assert creation invariants."""
        assert self.epoch > 0, "Epoch must be positive"
        assert self._energy() < 0, "Bound orbit requires negative energy"
        assert self._angular_momentum() > 0, "Angular momentum must be positive"
    
    def _energy(self) -> float:
        """Specific orbital energy (km²/s²)."""
        mu = 398600.4418  # Earth GM
        r = sqrt(sum(x*x for x in self.position))
        v_sq = sum(v*v for v in self.velocity)
        return v_sq / 2 - mu / r
    
    def _angular_momentum(self) -> float:
        """Magnitude of specific angular momentum."""
        h = (
            self.position[1] * self.velocity[2] - self.position[2] * self.velocity[1],
            self.position[2] * self.velocity[0] - self.position[0] * self.velocity[2],
            self.position[0] * self.velocity[1] - self.position[1] * self.velocity[0]
        )
        return sqrt(sum(x*x for x in h))

def validate_propagation_step(
    state_before: OrbitalState,
    state_after: OrbitalState,
    dt: float,
    tolerance: float = 1e-6
) -> bool:
    """
    Loop invariant: Energy and angular momentum conserved during propagation.
    Precondition: dt > 0, states are valid
    Postcondition: Physical laws preserved within tolerance
    """
    assert dt > 0, "Time step must be positive"
    
    # Invariant 1: Energy conservation (no external forces)
    e_before = state_before._energy()
    e_after = state_after._energy()
    energy_error = abs((e_after - e_before) / e_before)
    
    # Invariant 2: Angular momentum conservation (central force)
    h_before = state_before._angular_momentum()
    h_after = state_after._angular_momentum()
    momentum_error = abs((h_after - h_before) / h_before)
    
    return energy_error < tolerance and momentum_error < tolerance

def prove_orbit_closure(states: list[OrbitalState], period_estimate: float) -> bool:
    """Verify that orbit closes on itself within one period."""
    if len(states) < 2:
        return False
    initial = states[0]
    final = states[-1]
    pos_diff = sqrt(sum((a-b)**2 for a, b in zip(initial.position, final.position)))
    return pos_diff < 1.0  # Within 1 km closure tolerance