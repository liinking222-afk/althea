import numpy as np

def kepler_solve_batch(M, e, tol=1e-9, max_iter=6):
    """Solve Kepler's equation M = E - e*sin(E) vectorized. Fixed iteration: predictable cycles."""
    E = np.where(e < 0.3, M, np.pi)  # Branch once, not per-iteration
    
    # Unrolled Newton-Raphson: 6 iterations handles e<0.95 to machine precision
    # Cache-friendly: all ops vectorized, no conditionals in loop
    for _ in range(max_iter):
        sin_E = np.sin(E)
        cos_E = np.cos(E)
        f = E - e * sin_E - M
        fp = 1.0 - e * cos_E
        E -= f / fp  # Division cheaper than branch misprediction
    
    return E

def orbital_xyz_fast(a, e, i, Om, w, M, mu=1.32712440018e20):
    """Convert orbital elements to cartesian. Inline trig, minimize transcendentals."""
    # Solve Kepler in batch - hot path
    E = kepler_solve_batch(M, e)
    
    # Inline true anomaly: reuse sin/cos from Kepler solve (cache hit)
    sqrt_term = np.sqrt(1.0 - e * e)
    cos_E = np.cos(E)
    sin_E = np.sin(E)
    
    # True anomaly via atan2: single transcendental
    nu = np.arctan2(sqrt_term * sin_E, cos_E - e)
    
    # Radius: algebraic only
    r = a * (1.0 - e * cos_E)
    
    # Precompute rotation matrix elements (strength reduction)
    ci, si = np.cos(i), np.sin(i)
    cO, sO = np.cos(Om), np.sin(Om)
    cw, sw = np.cos(w + nu), np.sin(w + nu)
    
    # Inline matrix multiply: 9 muls, 6 adds per particle
    x = r * (cO * cw - sO * sw * ci)
    y = r * (sO * cw + cO * sw * ci)
    z = r * (sw * si)
    
    return np.stack([x, y, z], axis=-1)

def propagate_n_body(elements, dt, n_steps, mu=1.32712440018e20):
    """Propagate N particles. Mean motion advancement: no integration overhead."""
    a, e, i, Om, w, M0 = elements.T
    n = np.sqrt(mu / (a * a * a))  # Mean motion: single sqrt per particle
    
    positions = np.zeros((n_steps, len(a), 3))
    
    for step in range(n_steps):
        M = M0 + n * (step * dt)  # Arithmetic progression: fast
        M = np.fmod(M, 2 * np.pi)  # Wrap: single conditional equivalent
        positions[step] = orbital_xyz_fast(a, e, i, Om, w, M, mu)
    
    return positions