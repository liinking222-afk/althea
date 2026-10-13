"""
Fractal Loop Invariant Validator
Dijkstra-style formal verification for iteration correctness
"""

from dataclasses import dataclass
from typing import Tuple, Optional


@dataclass(frozen=True)
class Invariant:
    """Immutable invariant state - prerequisites for each iteration"""
    max_iter: int
    escape_radius_sq: float
    iteration: int
    z_magnitude_sq: float
    
    def holds(self) -> bool:
        """Check if invariant conditions are satisfied"""
        return (
            0 <= self.iteration <= self.max_iter and
            self.escape_radius_sq > 0 and
            self.max_iter > 0 and
            self.z_magnitude_sq >= 0
        )
    
    def escaped(self) -> bool:
        """Termination condition: has z escaped?"""
        return self.z_magnitude_sq > self.escape_radius_sq
    
    def exhausted(self) -> bool:
        """Termination condition: iterations exhausted?"""
        return self.iteration >= self.max_iter


def verify_iteration_step(
    before: Invariant,
    z_real: float,
    z_imag: float
) -> Tuple[bool, Optional[Invariant]]:
    """
    Verify single iteration maintains invariants.
    Returns (valid, next_state) where valid indicates correctness.
    """
    if not before.holds():
        return False, None
    
    if before.escaped() or before.exhausted():
        return True, before  # Termination conditions valid
    
    # Compute next magnitude squared (formal step)
    next_mag_sq = z_real * z_real + z_imag * z_imag
    
    # Construct post-condition state
    after = Invariant(
        max_iter=before.max_iter,
        escape_radius_sq=before.escape_radius_sq,
        iteration=before.iteration + 1,
        z_magnitude_sq=next_mag_sq
    )
    
    # Post-condition must hold
    return after.holds(), after


def certify_fractal_loop(
    max_iter: int,
    escape_radius: float = 2.0
) -> Invariant:
    """Initialize certified invariant for fractal computation"""
    inv = Invariant(
        max_iter=max_iter,
        escape_radius_sq=escape_radius * escape_radius,
        iteration=0,
        z_magnitude_sq=0.0
    )
    assert inv.holds(), "Initial invariant must hold"
    return inv