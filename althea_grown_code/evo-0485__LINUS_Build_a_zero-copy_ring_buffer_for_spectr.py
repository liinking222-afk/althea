import numpy as np
from numpy.typing import NDArray

class SpectralRingBuffer:
    """Zero-copy ring buffer for streaming spectral analysis.
    
    Monolithic fixed-size buffer with head pointer arithmetic.
    No dynamic allocation after initialization. Data structure IS the algorithm.
    """
    
    def __init__(self, window_size: int, dtype=np.float64):
        self.size = window_size
        self.buffer = np.zeros(window_size * 2, dtype=dtype)
        self.head = 0
        self.count = 0
        
    def push(self, samples: NDArray) -> None:
        """Write samples via head pointer, wrapping at 2*size."""
        n = len(samples)
        if n > self.size:
            samples = samples[-self.size:]
            n = self.size
            
        end = self.head + n
        
        if end <= len(self.buffer):
            self.buffer[self.head:end] = samples
        else:
            split = len(self.buffer) - self.head
            self.buffer[self.head:] = samples[:split]
            self.buffer[:end - len(self.buffer)] = samples[split:]
            
        self.head = end % len(self.buffer)
        self.count = min(self.count + n, self.size)
        
    def get_window(self) -> NDArray:
        """Return view into contiguous window without copy."""
        if self.count < self.size:
            return None
            
        start = (self.head - self.size) % len(self.buffer)
        
        if start + self.size <= len(self.buffer):
            return self.buffer[start:start + self.size]
        else:
            np.copyto(self.buffer[self.size:self.size * 2], 
                     self.buffer[:self.size])
            return self.buffer[self.size:self.size * 2]
    
    def ready(self) -> bool:
        """Check if full window available."""
        return self.count >= self.size