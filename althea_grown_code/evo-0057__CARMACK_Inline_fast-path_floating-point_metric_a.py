import struct
import time
from array import array

class MetricAggregator:
    __slots__ = ('_buf', '_write_idx', '_capacity', '_sum', '_sum_sq', '_count', '_min', '_max')
    
    def __init__(self, capacity=64):
        # Cache-line aligned ring buffer for hot metrics (integrity/coherence/link)
        self._capacity = capacity
        self._buf = array('f', [0.0] * capacity)  # contiguous float32 for cache locality
        self._write_idx = 0
        # Running accumulators - no recomputation on read
        self._sum = 0.0
        self._sum_sq = 0.0
        self._count = 0
        self._min = float('inf')
        self._max = float('-inf')
    
    def push(self, value):
        # Inline hot path: O(1) push with running stats update
        old_val = self._buf[self._write_idx]
        self._buf[self._write_idx] = value
        self._write_idx = (self._write_idx + 1) & (self._capacity - 1)  # bitwise mod for power-of-2
        
        if self._count < self._capacity:
            self._count += 1
        else:
            # Evict old value from accumulators
            self._sum -= old_val
            self._sum_sq -= old_val * old_val
        
        # Accumulate new value
        self._sum += value
        self._sum_sq += value * value
        self._min = value if value < self._min else self._min
        self._max = value if value > self._max else self._max
    
    def snapshot(self):
        # Sub-microsecond read path: no iteration, pure arithmetic
        if self._count == 0:
            return (0.0, 0.0, 0.0, 0.0, 0.0)
        
        mean = self._sum / self._count
        variance = (self._sum_sq / self._count) - (mean * mean)
        stddev = variance ** 0.5 if variance > 0.0 else 0.0
        
        return (mean, stddev, self._min, self._max, float(self._count))

# Triple-buffer for integrity/coherence/link - zero allocation in update loop
_metrics = {
    'integrity': MetricAggregator(64),
    'coherence': MetricAggregator(64),
    'link': MetricAggregator(64)
}

def update_topbar_metric(metric_name, value):
    _metrics[metric_name].push(value)

def get_topbar_display():
    # Single function call for full dashboard - 3 dict lookups, 3 method calls
    return {k: v.snapshot() for k, v in _metrics.items()}