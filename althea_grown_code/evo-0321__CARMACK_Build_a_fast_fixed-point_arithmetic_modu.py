import numpy as np
from numba import njit, int32, float32

@njit(fastmath=True, cache=True)
def fixed_to_float(x: int32, shift: int32) -> float32:
    """Convert fixed-point to float. shift typically 16 for Q16.16 format."""
    return float32(x) * (1.0 / float32(1 << shift))

@njit(fastmath=True, cache=True)
def float_to_fixed(x: float32, shift: int32) -> int32:
    """Convert float to fixed-point. Inline multiply then cast."""
    return int32(x * float32(1 << shift))

@njit(fastmath=True, cache=True, inline='always')
def mul_fixed(a: int32, b: int32, shift: int32) -> int32:
    """Multiply two fixed-point numbers. Result >> shift to renormalize."""
    return int32((int64(a) * int64(b)) >> shift)

@njit(fastmath=True, cache=True)
def transform_coords_batch(x_data, y_data, x_min, x_max, y_min, y_max, 
                           width: int32, height: int32, shift: int32):
    """Batch transform float coords to pixel space using fixed-point math.
    Cache-friendly: sequential access, predictable branches, vectorizable."""
    n = len(x_data)
    px = np.empty(n, dtype=np.int32)
    py = np.empty(n, dtype=np.int32)
    
    x_range = x_max - x_min
    y_range = y_max - y_min
    
    x_scale_fixed = float_to_fixed(float32(width) / x_range, shift)
    y_scale_fixed = float_to_fixed(float32(height) / y_range, shift)
    
    for i in range(n):
        x_norm = float_to_fixed((x_data[i] - x_min) / x_range, shift)
        y_norm = float_to_fixed((y_data[i] - y_min) / y_range, shift)
        
        px[i] = mul_fixed(x_norm, x_scale_fixed, shift)
        py[i] = height - mul_fixed(y_norm, y_scale_fixed, shift)
    
    return px, py