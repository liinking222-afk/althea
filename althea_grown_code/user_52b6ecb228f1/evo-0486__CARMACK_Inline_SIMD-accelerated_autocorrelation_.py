import numpy as np
from numba import njit, prange

@njit(fastmath=True, cache=True)
def _autocorr_kernel(x, out, n, max_lag):
    """Inline autocorrelation kernel. No bounds checks. Pure cycles."""
    mean = 0.0
    for i in range(n):
        mean += x[i]
    mean /= n
    
    # Variance computation - single pass, cache-friendly
    var = 0.0
    for i in range(n):
        dev = x[i] - mean
        var += dev * dev
    
    # Early exit on degenerate signal
    if var < 1e-10:
        for lag in range(max_lag):
            out[lag] = 0.0
        return
    
    # Autocorrelation lags - aggressive loop fusion
    for lag in prange(max_lag):
        acc = 0.0
        limit = n - lag
        for i in range(limit):
            acc += (x[i] - mean) * (x[i + lag] - mean)
        out[lag] = acc / var

@njit(fastmath=True, cache=True, parallel=True)
def batch_autocorr(signals, max_lag):
    """Batch autocorr for spectral window streaming. Zero-copy output."""
    n_signals, signal_len = signals.shape
    out = np.empty((n_signals, max_lag), dtype=np.float64)
    
    for i in prange(n_signals):
        _autocorr_kernel(signals[i], out[i], signal_len, max_lag)
    
    return out

def autocorr_spectral_preprocess(signal, window_size=512, hop=256, max_lag=64):
    """Streaming autocorrelation preprocessing. Reuses buffer geometry."""
    n = len(signal)
    n_windows = (n - window_size) // hop + 1
    
    # Pre-allocate exact buffer - no realloc, cache-aligned
    windows = np.lib.stride_tricks.as_strided(
        signal,
        shape=(n_windows, window_size),
        strides=(signal.strides[0] * hop, signal.strides[0])
    )
    
    return batch_autocorr(windows, max_lag)