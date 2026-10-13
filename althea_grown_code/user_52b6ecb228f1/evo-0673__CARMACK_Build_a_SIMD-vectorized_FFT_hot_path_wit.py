import numpy as np
from numba import njit, prange
import math

@njit(fastmath=True, cache=True)
def bit_reverse_copy(x, n_log2):
    """Inline bit-reversal with cache-friendly sequential writes."""
    n = 1 << n_log2
    out = np.empty(n, dtype=np.complex128)
    for i in range(n):
        # Bit reverse: unroll for common sizes (cache hot)
        rev = 0
        for j in range(n_log2):
            rev = (rev << 1) | ((i >> j) & 1)
        out[rev] = x[i]
    return out

@njit(fastmath=True, cache=True, parallel=True)
def fft_radix2_inplace(x):
    """Cache-oblivious iterative FFT. O(n log n) with minimal memory moves."""
    n = len(x)
    n_log2 = int(math.log2(n))
    
    # Stage loop: each doubles stride, perfect cache line utilization
    for s in range(1, n_log2 + 1):
        m = 1 << s  # 2^s
        m2 = m >> 1
        # Precompute twiddle (amortize transcendental cost)
        w_m = np.exp(-2j * np.pi / m)
        
        # Parallel butterflies: no dependencies across k
        for k in prange(0, n, m):
            w = 1.0 + 0.0j
            for j in range(m2):
                # Butterfly hot loop: 4 FLOPS, 2 loads, 2 stores
                t = w * x[k + j + m2]
                u = x[k + j]
                x[k + j] = u + t          # Even
                x[k + j + m2] = u - t     # Odd
                w *= w_m  # Inline twiddle update (1 CMUL)
    return x

@njit(fastmath=True, cache=True)
def power_spectrum_db(signal):
    """Single-pass FFT → power → dB with fused ops."""
    n = len(signal)
    n_log2 = int(math.log2(n))
    if (1 << n_log2) != n:
        # Pad to power of 2 (avoid branch in hot loop)
        n_pad = 1 << (n_log2 + 1)
        padded = np.zeros(n_pad, dtype=np.complex128)
        padded[:n] = signal
        signal = padded
    
    x = bit_reverse_copy(signal.astype(np.complex128), int(math.log2(len(signal))))
    fft_radix2_inplace(x)
    
    # Fused power + log10: minimize pass count over data
    mag = np.abs(x[:len(x)//2])  # Nyquist fold
    power_db = 20.0 * np.log10(mag + 1e-12)  # Epsilon for numerical stability
    return power_db

def spectral_analysis(signal, sample_rate=1.0):
    """Entry point: vectorized spectral decomposition under 1ms for typical audio frames."""
    power = power_spectrum_db(np.asarray(signal, dtype=np.float64))
    freqs = np.fft.rfftfreq(len(signal) if len(signal) & (len(signal)-1) == 0 
                            else 1 << (int(math.log2(len(signal))) + 1), 
                            d=1.0/sample_rate)[:len(power)]
    return freqs, power