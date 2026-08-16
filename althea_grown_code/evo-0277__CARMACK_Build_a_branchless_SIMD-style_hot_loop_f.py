import array
import struct

class RecursionSaturationDetector:
    """Cache-aligned recursion depth tracker. O(1) saturation check, zero heap alloc."""
    
    __slots__ = ('_state', '_thresholds', '_history_ring', '_write_idx', '_mask')
    
    def __init__(self, max_depth=32, window=16):
        # Power-of-2 for bit-mask modulo, cache line friendly
        self._mask = window - 1  # branchless ring buffer index
        self._state = array.array('I', [0] * 8)  # unsigned int: [depth, saturated, trigger_count, reserved...]
        self._thresholds = array.array('I', [max_depth, max_depth >> 1, max_depth >> 2, 0])
        self._history_ring = array.array('B', [0] * window)  # byte array for depth history
        self._write_idx = 0
    
    def push_depth(self, current_depth):
        """Hot path: inline-worthy depth tracking. No branches in critical section."""
        # Ring buffer write (branchless via mask)
        self._history_ring[self._write_idx] = min(current_depth, 255)
        self._write_idx = (self._write_idx + 1) & self._mask
        
        # Update state[0] = current depth
        self._state[0] = current_depth
        
        # Saturation = depth >= threshold (produces 0 or 1)
        sat_bit = int(current_depth >= self._thresholds[0])
        self._state[1] = sat_bit
        
        # Increment trigger counter using saturation bit (branchless)
        self._state[2] += sat_bit
        
        return sat_bit
    
    def get_variance_estimate(self):
        """Fast variance proxy: max-min range over ring buffer. Single pass."""
        if not self._history_ring:
            return 0
        
        min_val = 255
        max_val = 0
        
        # Unrolled scan (compiler-friendly)
        for i in range(0, len(self._history_ring), 4):
            v0, v1, v2, v3 = self._history_ring[i], self._history_ring[i+1], self._history_ring[i+2], self._history_ring[i+3]
            min_val = min(min_val, v0, v1, v2, v3)
            max_val = max(max_val, v0, v1, v2, v3)
        
        return max_val - min_val
    
    def is_saturated(self):
        """Inline candidate: single int load."""
        return self._state[1] != 0
    
    def should_pivot(self):
        """Decision function: saturation + low variance = stuck in loop."""
        return self._state[1] and (self.get_variance_estimate() < 3)
    
    def reset(self):
        """Zero-cost reset via memset equivalent."""
        for i in range(len(self._state)):
            self._state[i] = 0
        self._write_idx = 0