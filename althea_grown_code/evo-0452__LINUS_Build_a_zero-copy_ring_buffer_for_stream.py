import numpy as np
from collections import namedtuple

Window = namedtuple('Window', ['data', 'start_idx', 'end_idx'])

class SignalRingBuffer:
    """Zero-copy ring buffer for BCI streaming data. No reallocation, no shifts."""
    
    __slots__ = ('_buf', '_capacity', '_head', '_tail', '_size', '_channels')
    
    def __init__(self, capacity: int, n_channels: int = 1):
        self._capacity = capacity
        self._channels = n_channels
        self._buf = np.zeros((capacity, n_channels), dtype=np.float32)
        self._head = 0
        self._tail = 0
        self._size = 0
    
    def append(self, sample: np.ndarray) -> None:
        """O(1) append. Overwrites oldest if full."""
        self._buf[self._tail] = sample
        self._tail = (self._tail + 1) % self._capacity
        if self._size < self._capacity:
            self._size += 1
        else:
            self._head = (self._head + 1) % self._capacity
    
    def append_batch(self, samples: np.ndarray) -> None:
        """Batch append with minimal bounds checking."""
        n = len(samples)
        if n >= self._capacity:
            self._buf[:] = samples[-self._capacity:]
            self._head = 0
            self._tail = 0
            self._size = self._capacity
            return
        
        space_to_end = self._capacity - self._tail
        if n <= space_to_end:
            self._buf[self._tail:self._tail + n] = samples
        else:
            self._buf[self._tail:] = samples[:space_to_end]
            self._buf[:n - space_to_end] = samples[space_to_end:]
        
        self._tail = (self._tail + n) % self._capacity
        self._size = min(self._size + n, self._capacity)
        if self._size == self._capacity:
            self._head = self._tail
    
    def get_window(self, n_samples: int) -> np.ndarray:
        """Return last n samples as contiguous view or copy."""
        if n_samples > self._size:
            n_samples = self._size
        if n_samples == 0:
            return np.array([]).reshape(0, self._channels)
        
        start = (self._head + self._size - n_samples) % self._capacity
        if start + n_samples <= self._capacity:
            return self._buf[start:start + n_samples]
        else:
            wrap = (start + n_samples) - self._capacity
            return np.vstack([self._buf[start:], self._buf[:wrap]])
    
    @property
    def size(self) -> int:
        return self._size
    
    def clear(self) -> None:
        self._head = self._tail = self._size = 0