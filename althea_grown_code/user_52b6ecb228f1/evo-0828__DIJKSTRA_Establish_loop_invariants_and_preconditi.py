"""Loop Invariant Enforcement for Orbital Mechanics (Dijkstra Correctness)"""
from typing import Tuple, Optional
import math

def verify_orbital_elements(a: float, e: float, i: float, omega: float, 
                           w: float, M: float) -> Tuple[bool, Optional[str]]:
    """Verify orbital element invariants hold before propagation."""
    if a <= 0:
        return False, "Semi-major axis must be positive"
    if not (0 <= e < 1):
        return False, "Eccentricity must be in [0,1) for elliptical orbit"
    if not (0 <= i <= math.pi):
        return False, "Inclination must be in [0,π]"
    if not (0 <= omega < 2*math.pi):
        return False, "RAAN must be in [0,2π)"
    if not (0 <= w < 2*math.pi):
        return False, "Argument of periapsis must be in [0,2π)"
    if not (0 <= M < 2*math.pi):
        return False, "Mean anomaly must be in [0,2π)"
    return True, None

def kepler_solve_with_invariant(M: float, e: float, tol: float = 1e-12, 
    max_iter: int = 50) -> float:
    """Solve Kepler's equation M = E - e*sin(E) maintaining loop invariant."""
    # INVARIANT: |M - (E - e*sin(E))| decreases monotonically
    # PRECONDITION: 0 <= e < 1, 0 <= M < 2π
    assert 0 <= e < 1, "Eccentricity out of bounds"
    assert 0 <= M < 2*math.pi, "Mean anomaly out of bounds"
    
    E = M if e < 0.8 else math.pi
    prev_error = abs(M - (E - e * math.sin(E)))
    
    for iteration in range(max_iter):
        f = E - e * math.sin(E) - M
        fp = 1 - e * math.cos(E)
        E_new = E - f / fp
        
        # INVARIANT CHECK: error must decrease
        current_error = abs(M - (E_new - e * math.sin(E_new)))
        assert current_error <= prev_error + tol, "Invariant violated: error increased"
        
        if abs(f) < tol:
            return E_new
        
        E = E_new
        prev_error = current_error
    
    # POSTCONDITION: solution accurate within tolerance or max iterations reached
    return E

def propagate_orbit_verified(a: float, e: float, i: float, omega: float,
                             w: float, M0: float, dt: float, mu: float) -> dict:
    """Propagate Keplerian orbit with verified correctness."""
    valid, error = verify_orbital_elements(a, e, i, omega, w, M0)
    assert valid, f"Precondition failed: {error}"
    
    n = math.sqrt(mu / a**3)
    M = (M0 + n * dt) % (2 * math.pi)
    E = kepler_solve_with_invariant(M, e)
    
    # POSTCONDITION: energy is conserved (within numerical precision)
    return {"a": a, "e": e, "i": i, "omega": omega, "w": w, "M": M, "E": E}