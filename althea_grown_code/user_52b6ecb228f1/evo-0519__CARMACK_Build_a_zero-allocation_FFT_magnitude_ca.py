import numpy as np
from typing import Optional

class FFTHotCache:
    """Carmack-style FFT cache: precompute twiddles, inline butterflies, minimize alloc."""
    
    __slots__ = ('_size', '_twiddles_re', '_twiddles_im', '_bit_reverse', '_mag_cache')
    
    def __init__(self, max_size: int = 8192):
        # Power of 2 ceiling for radix-2 FFT
        self._size = 1 << (max_size - 1).bit_length()
        n = self._size
        
        # Precompute twiddle factors (exp(-2πi k/N)) - cache locality matters
        angles = -2.0 * np.pi * np.arange(n // 2, dtype=np.float32) / n
        self._twiddles_re = np.cos(angles)  # Real part inline
        self._twiddles_im = np.sin(angles)  # Imag part inline
        
        # Bit-reversal permutation LUT for in-place FFT
        self._bit_reverse = np.array([
            int(bin(i)[2:].zfill((n - 1).bit_length())[::-1], 2) 
            for i in range(n)
        ], dtype=np.int32)
        
        # Reusable magnitude buffer - zero heap allocs in hot loop
        self._mag_cache = np.zeros(n // 2 + 1, dtype=np.float32)
    
    def spectral_magnitude(self, signal: np.ndarray) -> np.ndarray:
        """Compute FFT magnitude with zero-copy where possible. Returns cached array."""
        n = len(signal)
        if n > self._size:
            n = self._size  # Truncate
        
        # Zero-pad to power of 2 in-place if needed
        if n < self._size:
            padded = np.zeros(self._size, dtype=np.complex64)
            padded[:n] = signal[:n]
        else:
            padded = signal[:self._size].astype(np.complex64, copy=True)
        
        # Bit-reverse permutation (cache-friendly sequential write)
        padded[:] = padded[self._bit_reverse]
        
        # Radix-2 Cooley-Tukey with inlined butterfly (minimize function call overhead)
        m = 1
        stages = (self._size - 1).bit_length()
        for _ in range(stages):
            m2 = m * 2
            twiddle_stride = self._size // m2
            for k in range(0, self._size, m2):
                for j in range(m):
                    t_idx = j * twiddle_stride
                    tw_re, tw_im = self._twiddles_re[t_idx], self._twiddles_im[t_idx]
                    # Inline butterfly operation - manual complex multiply
                    u = padded[k + j]
                    t_re = tw_re * padded[k + j + m].real - tw_im * padded[k + j + m].imag
                    t_im = tw_re * padded[k + j + m].imag + tw_im * padded[k + j + m].real
                    padded[k + j] = u + (t_re + 1j * t_im)
                    padded[k + j + m] = u - (t_re + 1j * t_im)
            m = m2
        
        # Magnitude: sqrt(re^2 + im^2) - write to cache buffer (zero alloc)
        half = self._size // 2 + 1
        np.abs(padded[:half], out=self._mag_cache)
        return self._mag_cache

# Global singleton instance - one allocation, reused across all spectral calls
_hot_fft = FFTHotCache()

def fast_spectral_magnitude(signal: np.ndarray) -> np.ndarray:
    """Cached FFT magnitude. Returns view of internal buffer - DO NOT MODIFY."""
    return _hot_fft.spectral_magnitude(signal)