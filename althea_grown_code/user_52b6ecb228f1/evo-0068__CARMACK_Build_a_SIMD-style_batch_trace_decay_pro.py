import numpy as np
from numba import jit, float32, int32

@jit(nopython=True, fastmath=True, cache=True)
def decay_traces_hot(weights, ages, base_decay, volatility_map, dt, out):
    """Inline decay kernel. No branches in inner loop. Pure arithmetic."""
    n = weights.shape[0]
    inv_dt = 1.0 / dt if dt > 0.0 else 1.0
    
    for i in range(n):
        # Cache-local reads: sequential access pattern
        w = weights[i]
        age = ages[i]
        vol = volatility_map[i]
        
        # Inline decay math: exponential approximation via Taylor O(3)
        # e^(-x) ≈ 1 - x + x²/2 - x³/6 for small x
        decay_rate = base_decay * (1.0 + vol * 0.5)  # volatility modulates rate
        x = decay_rate * age * inv_dt
        x2 = x * x
        decay_factor = 1.0 - x + 0.5 * x2 - 0.16666667 * x * x2
        
        # Clamp to [0, 1] without branch (min/max are SIMD-friendly)
        decay_factor = max(0.0, min(1.0, decay_factor))
        
        # Write result: sequential stride
        out[i] = w * decay_factor

@jit(nopython=True, fastmath=True, cache=True)
def update_ages_hot(ages, dt):
    """Increment all ages. Pure vectorizable operation."""
    n = ages.shape[0]
    for i in range(n):
        ages[i] += dt

class TraceDecayEngine:
    def __init__(self, capacity=4096):
        self.capacity = capacity
        self.weights = np.ones(capacity, dtype=np.float32)
        self.ages = np.zeros(capacity, dtype=np.float32)
        self.volatility = np.random.uniform(0.8, 1.2, capacity).astype(np.float32)
        self.output = np.zeros(capacity, dtype=np.float32)
        self.base_decay = 0.1
    
    def tick(self, dt=0.016):  # 60 FPS frame time default
        """Main hot loop: <100μs for 4K traces on modern CPU."""
        decay_traces_hot(self.weights, self.ages, self.base_decay, 
                        self.volatility, dt, self.output)
        update_ages_hot(self.ages, dt)
        self.weights[:] = self.output  # Swap buffers
        return self.output
    
    def set_trace(self, idx, weight=1.0, volatility=1.0):
        """Cold path: update single trace."""
        if 0 <= idx < self.capacity:
            self.weights[idx] = weight
            self.ages[idx] = 0.0
            self.volatility[idx] = volatility