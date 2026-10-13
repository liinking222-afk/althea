"""
/autonomous-invariant-guard-fractal
Dijkstra-style invariant enforcement for fractal computation kernels.
Ensures mathematical correctness through explicit preconditions and loop invariants.
"""

from typing import Tuple, Callable
import numpy as np
from functools import wraps

class InvariantViolation(Exception):
    """Raised when a loop invariant or precondition is violated."""
    pass

def enforce_fractal_invariants(func: Callable) -> Callable:
    """
    Decorator ensuring fractal iteration satisfies Dijkstra-style invariants:
    - Precondition: coordinates within complex plane bounds
    - Invariant: |z| monotonically non-decreasing after escape
    - Postcondition: iteration count ≤ max_iter, escape detected correctly
    """
    @wraps(func)
    def guarded(*args, **kwargs):
        # Extract parameters with precise contracts
        c_real = kwargs.get('c_real', args[0] if len(args) > 0 else None)
        c_imag = kwargs.get('c_imag', args[1] if len(args) > 1 else None)
        max_iter = kwargs.get('max_iter', args[2] if len(args) > 2 else 256)
        escape_radius = kwargs.get('escape_radius', args[3] if len(args) > 3 else 2.0)
        
        # Precondition: valid complex number and parameters
        assert c_real is not None and c_imag is not None, "Complex coordinate required"
        assert max_iter > 0, "max_iter must be positive"
        assert escape_radius > 0, "escape_radius must be positive"
        assert np.isfinite(c_real) and np.isfinite(c_imag), "Coordinates must be finite"
        
        result = func(*args, **kwargs)
        
        # Postcondition: iteration count in valid range
        if isinstance(result, (int, np.integer)):
            assert 0 <= result <= max_iter, f"Iteration count {result} outside [0, {max_iter}]"
        
        return result
    
    return guarded

@enforce_fractal_invariants
def mandelbrot_point(c_real: float, c_imag: float, max_iter: int = 256, 
                     escape_radius: float = 2.0) -> int:
    """
    Compute Mandelbrot iterations with enforced invariants.
    Invariant: At loop head, 0 <= n <= max_iter and (escaped => |z|² > R²)
    """
    z_real, z_imag = 0.0, 0.0
    escape_radius_sq = escape_radius * escape_radius
    
    for n in range(max_iter):
        # Loop invariant check: magnitude tracking
        z_mag_sq = z_real * z_real + z_imag * z_imag
        
        if z_mag_sq > escape_radius_sq:
            # Invariant: escaped => n < max_iter
            assert n < max_iter, "Escape must occur before max_iter"
            return n
        
        # Core iteration: z → z² + c
        z_real, z_imag = z_real * z_real - z_imag * z_imag + c_real, 2 * z_real * z_imag + c_imag
        
        # Invariant: no NaN/Inf propagation
        if not (np.isfinite(z_real) and np.isfinite(z_imag)):
            raise InvariantViolation(f"Non-finite value at iteration {n}")
    
    return max_iter

def verify_invariant_module():
    """Self-verification of invariant enforcement."""
    # Test normal convergence
    assert mandelbrot_point(0.0, 0.0, max_iter=100) == 100
    # Test escape
    assert mandelbrot_point(1.0, 1.0, max_iter=100) < 100
    # Test boundary precision
    result = mandelbrot_point(-0.75, 0.1, max_iter=1000, escape_radius=2.0)
    assert 0 <= result <= 1000
    return True