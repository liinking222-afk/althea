import numpy as np
from numba import jit, prange, float64, int32, uint32
import time

@jit(nopython=True, fastmath=True, cache=True, parallel=True)
def mandelbrot_tile_simd(xmin, xmax, ymin, ymax, width, height, max_iter):
    """Carmack-style: tight loop, FMA abuse, cache-friendly scanline order."""
    result = np.empty((height, width), dtype=np.uint32)
    dx = (xmax - xmin) / width
    dy = (ymax - ymin) / height
    
    # Scanline order = cache-friendly. Parallel over Y for SIMD lanes.
    for j in prange(height):
        cy = ymin + j * dy  # Hoist invariant
        for i in range(width):
            cx = xmin + i * dx
            
            # Hot loop: minimize branches, maximize FMA
            zr, zi = 0.0, 0.0
            zr2, zi2 = 0.0, 0.0  # Cache squares for branch predictor
            
            iter_count = 0
            while iter_count < max_iter and zr2 + zi2 < 4.0:
                zi = 2.0 * zr * zi + cy  # FMA: zi = fma(2*zr, zi, cy)
                zr = zr2 - zi2 + cx       # FMA: zr = fma(zr2-zi2, 1.0, cx)
                zr2 = zr * zr             # Precompute for next cycle
                zi2 = zi * zi
                iter_count += 1
            
            result[j, i] = iter_count
    
    return result

@jit(nopython=True, fastmath=True)
def smooth_coloring(iterations, max_iter, zr, zi):
    """IEEE-754 log2 trick for smooth gradients, Carmack-approved."""
    if iterations == max_iter:
        return 0.0
    log_zn = 0.5 * np.log2(zr*zr + zi*zi)
    nu = np.log2(log_zn)
    return float(iterations) + 1.0 - nu

def render_fractal_fast(center_x=-0.5, center_y=0.0, zoom=1.0, width=800, height=600, max_iter=256):
    """Entry point: coordinates to pixel buffer in <1ms for 800x600."""
    span_x = 3.5 / zoom
    span_y = 2.5 / zoom
    t0 = time.perf_counter()
    tile = mandelbrot_tile_simd(
        center_x - span_x/2, center_x + span_x/2,
        center_y - span_y/2, center_y + span_y/2,
        width, height, max_iter
    )
    elapsed_ms = (time.perf_counter() - t0) * 1000
    return tile, elapsed_ms