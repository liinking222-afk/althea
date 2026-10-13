import numpy as np
from numba import jit, prange
import math

@jit(nopython=True, fastmath=True, cache=True)
def _bit_reverse_copy(x, n):
    """Inline bit reversal - O(n log n) but cache-friendly sequential write"""
    out = np.empty(n, dtype=np.complex128)
    bits = int(math.log2(n))
    for i in range(n):
        rev = 0
        for j in range(bits):
            rev = (rev << 1) | ((i >> j) & 1)
        out[rev] = x[i]
    return out

@jit(nopython=True, fastmath=True, parallel=True, cache=True)
def _fft_radix2_inplace(x):
    """Cooley-Tukey radix-2 decimation-in-time. Cache-optimized butterfly stride."""
    n = len(x)
    # Stages: log2(n) iterations, butterfly width doubles each stage
    stages = int(math.log2(n))
    for s in prange(stages):
        m = 1 << (s + 1)  # 2^(s+1) - butterfly span
        half_m = m >> 1
        # Twiddle factor w_m = e^(-2πi/m) - precompute once per stage
        theta = -2.0 * math.pi / m
        wr = math.cos(theta)
        wi = math.sin(theta)
        for k in range(0, n, m):  # Process blocks of size m
            w = 1.0 + 0.0j
            for j in range(half_m):  # Butterfly inner loop
                t = w * x[k + j + half_m]  # Complex multiply - 4 FLOPs
                u = x[k + j]
                x[k + j] = u + t  # Butterfly add
                x[k + j + half_m] = u - t  # Butterfly subtract
                # Update twiddle: w *= w_m - avoid expensive exp()
                w = complex(wr * w.real - wi * w.imag, wr * w.imag + wi * w.real)

def fft_carmack(signal):
    """Zero-copy FFT for power-of-2 signals. Returns spectral density."""
    n = len(signal)
    assert (n & (n - 1)) == 0, "Length must be power of 2"
    x = _bit_reverse_copy(np.asarray(signal, dtype=np.complex128), n)
    _fft_radix2_inplace(x)
    return np.abs(x) ** 2 / n  # Power spectral density - single sqrt saved vs abs

def spectral_analyze(signal, sample_rate=1.0):
    """Fast spectral analysis entry point. Returns (freqs, power)."""
    psd = fft_carmack(signal)
    freqs = np.fft.fftfreq(len(signal), d=1.0/sample_rate)
    return freqs[:len(freqs)//2], psd[:len(psd)//2]