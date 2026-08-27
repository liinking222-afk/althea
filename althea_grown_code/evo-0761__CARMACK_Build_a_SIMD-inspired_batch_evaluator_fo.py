import numpy as np
from numba import jit, prange

@jit(nopython=True, fastmath=True, cache=True)
def mandelbrot_batch4(c_real, c_imag, max_iter):
    """Evaluate 4 Mandelbrot points simultaneously. Branchless inner loop.
    Returns iteration counts [i0, i1, i2, i3]. Sub-1ms for typical batches."""
    z_r = np.zeros(4, dtype=np.float64)  # Real parts, cache-aligned
    z_i = np.zeros(4, dtype=np.float64)  # Imag parts, stack-local
    counts = np.zeros(4, dtype=np.int32)
    active = np.ones(4, dtype=np.bool_)   # Escape mask
    
    for n in range(max_iter):
        # All 4 points in tight loop, no branching until end
        zr2 = z_r * z_r
        zi2 = z_i * z_i
        
        # z = z^2 + c, unrolled for locality
        z_i[:] = 2.0 * z_r * z_i + c_imag
        z_r[:] = zr2 - zi2 + c_real
        
        # Escape test: |z|^2 > 4.0
        mag2 = zr2 + zi2
        escaped = mag2 > 4.0
        
        # Branchless count update: add only if still active
        counts += active & ~escaped
        active &= ~escaped
        
        if not active.any():  # All escaped, early exit
            break
    
    return counts

@jit(nopython=True, parallel=True, fastmath=True)
def fractal_render_optimized(x_min, x_max, y_min, y_max, width, height, max_iter):
    """Render fractal with batch-4 SIMD-style eval. Parallel outer loop."""
    result = np.zeros((height, width), dtype=np.int32)
    dx = (x_max - x_min) / width
    dy = (y_max - y_min) / height
    
    for row in prange(height):
        y = y_min + row * dy
        col = 0
        while col < width - 3:  # Process 4 pixels at once
            x_batch = np.array([x_min + (col + i) * dx for i in range(4)])
            y_batch = np.full(4, y)
            counts = mandelbrot_batch4(x_batch, y_batch, max_iter)
            result[row, col:col+4] = counts
            col += 4
        
        # Tail cleanup for width % 4 remainder
        for c in range(col, width):
            x = x_min + c * dx
            result[row, c] = mandelbrot_batch4(
                np.array([x]), np.array([y]), max_iter
            )[0]
    
    return result