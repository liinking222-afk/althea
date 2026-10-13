import numpy as np
from numba import jit, prange, float32, int32

@jit(nopython=True, fastmath=True, cache=True)
def sliding_variance_hot(signal: np.ndarray, window: int32, out: np.ndarray) -> None:
    """
    O(n) sliding variance via Welford's online algorithm.
    Cache-friendly sequential access. Branchless inner loop.
    Inlined mean/M2 updates. Pre-allocated output buffer.
    """
    n = signal.shape[0]
    if n < window:
        return
    
    # Prime the pump: initial window
    mean = float32(0.0)
    M2 = float32(0.0)
    inv_window = float32(1.0) / float32(window)
    
    for i in range(window):
        x = signal[i]
        delta = x - mean
        mean += delta * inv_window
        delta2 = x - mean
        M2 += delta * delta2
    
    out[window - 1] = M2 * inv_window
    
    # Slide: O(1) per step, rolling update
    for i in range(window, n):
        x_new = signal[i]
        x_old = signal[i - window]
        
        # Remove old sample contribution
        delta_old = x_old - mean
        mean -= delta_old * inv_window
        
        # Add new sample contribution
        delta_new = x_new - mean
        mean += delta_new * inv_window
        
        # Update M2 (sum of squared deviations)
        M2 += delta_new * (x_new - mean) - delta_old * (x_old - mean)
        
        out[i] = M2 * inv_window

@jit(nopython=True, parallel=True, fastmath=True)
def batch_channel_variance(channels: np.ndarray, window: int32) -> np.ndarray:
    """Parallel variance across EEG channels. SIMD via numba."""
    n_channels, n_samples = channels.shape
    result = np.zeros((n_channels, n_samples), dtype=np.float32)
    
    for ch in prange(n_channels):
        sliding_variance_hot(channels[ch], window, result[ch])
    
    return result

# Fast quality metric: variance stability indicates clean signal
@jit(nopython=True, fastmath=True, inline='always')
def signal_quality_score(variance_trace: np.ndarray, threshold: float32) -> float32:
    """Returns [0,1] quality. Low variance-of-variance = stable = good."""
    if variance_trace.shape[0] < 2:
        return float32(0.0)
    v_of_v = np.var(variance_trace)
    return float32(1.0) / (float32(1.0) + v_of_v / threshold)