import time
from collections import deque
from dataclasses import dataclass

@dataclass
class SynthEvent:
    __slots__ = ('pattern', 'timestamp')
    pattern: str
    timestamp: float

class SynthesisThrottle:
    __slots__ = ('ring', 'capacity', 'window_sec', 'threshold', 'pattern_counts')
    
    def __init__(self, capacity: int = 1024, window_sec: float = 300.0, threshold: int = 3):
        self.ring = deque(maxlen=capacity)
        self.capacity = capacity
        self.window_sec = window_sec
        self.threshold = threshold
        self.pattern_counts = {}
    
    def record(self, pattern: str) -> bool:
        now = time.time()
        event = SynthEvent(pattern, now)
        
        # Evict stale events from front
        cutoff = now - self.window_sec
        while self.ring and self.ring[0].timestamp < cutoff:
            old = self.ring.popleft()
            self.pattern_counts[old.pattern] = self.pattern_counts.get(old.pattern, 1) - 1
            if self.pattern_counts[old.pattern] <= 0:
                del self.pattern_counts[old.pattern]
        
        # Add new event
        self.ring.append(event)
        self.pattern_counts[pattern] = self.pattern_counts.get(pattern, 0) + 1
        
        # Check throttle condition
        return self.pattern_counts[pattern] > self.threshold
    
    def get_hot_patterns(self) -> list[tuple[str, int]]:
        return sorted(self.pattern_counts.items(), key=lambda x: x[1], reverse=True)
    
    def should_throttle(self, pattern: str) -> bool:
        return self.pattern_counts.get(pattern, 0) > self.threshold
    
    def reset(self):
        self.ring.clear()
        self.pattern_counts.clear()

# Global singleton instance
_throttle = SynthesisThrottle()

def check_synthesis_pattern(pattern: str) -> bool:
    """Returns True if pattern should be throttled (runaway detected)"""
    return _throttle.record(pattern)

def get_synthesis_stats() -> dict:
    return {
        'hot_patterns': _throttle.get_hot_patterns()[:10],
        'total_tracked': len(_throttle.ring),
        'capacity': _throttle.capacity
    }