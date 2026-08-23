import numpy as np
from numpy.typing import NDArray

def fft_carmack(x: NDArray[np.float32]) -> NDArray[np.complex64]:
    """Cache-optimized radix-2 FFT. Power-of-2 lengths only. Inline everything."""
    n = len(x)
    assert n & (n - 1) == 0, "n must be power of 2"
    
    # Bit-reverse permutation using lookup (precompute once per size in production)
    j = 0
    a = np.zeros(n, dtype=np.complex64)
    for i in range(n):
        a[j] = x[i]  # Copy to complex, bit-reversed
        m = n >> 1
        while j >= m and m:
            j -= m
            m >>= 1
        j += m
    
    # Butterfly loops: optimize cache locality by processing adjacent pairs
    # Twiddle factors computed on-the-fly (trade ALU for cache misses)
    stage = 1
    while stage < n:
        half_stage = stage
        stage <<= 1
        # Precompute twiddle for this stage (only log2(n) unique values)
        angle_step = -np.pi / half_stage  # -2π/stage normalized
        
        # Process butterflies in cache-friendly order
        for m in range(0, n, stage):
            # Tight inner loop: maximum instruction-level parallelism
            w = 1.0 + 0.0j
            w_step = np.exp(1j * angle_step)  # Once per stage block
            
            for k in range(half_stage):
                idx_even = m + k
                idx_odd = idx_even + half_stage
                
                # Classic Cooley-Tukey butterfly (minimize temp allocations)
                t = w * a[idx_odd]
                a[idx_odd] = a[idx_even] - t  # In-place update
                a[idx_even] += t
                
                w *= w_step  # Rotate twiddle
        
        # Move to next stage (doubles butterfly span)
    
    return a

# Vectorized wrapper for batch processing (amortize overhead)
def fft_batch(signals: NDArray[np.float32]) -> NDArray[np.complex64]:
    """Process multiple signals with minimal loop overhead."""
    return np.array([fft_carmack(sig) for sig in signals], dtype=np.complex64)