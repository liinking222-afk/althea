import time
from collections import defaultdict

class AutosynthPatternCounter:
    """Ring buffer pattern counter with fixed memory footprint."""
    
    def __init__(self, window_seconds=3600, max_patterns=256):
        self.window = window_seconds
        self.max_patterns = max_patterns
        self.ring_size = 1024
        
        # Core data structures - arrays for cache locality
        self.ring = [(0.0, "")] * self.ring_size
        self.head = 0
        self.counts = defaultdict(int)
        self.first_seen = {}
        self.last_seen = {}
        
    def record(self, pattern_id: str) -> dict:
        """Record pattern invocation, return stats. O(1) amortized."""
        now = time.time()
        
        # Evict old entry at head position
        old_ts, old_pattern = self.ring[self.head]
        if old_pattern and (now - old_ts) > self.window:
            self.counts[old_pattern] -= 1
            if self.counts[old_pattern] <= 0:
                del self.counts[old_pattern]
                del self.first_seen[old_pattern]
                del self.last_seen[old_pattern]
        
        # Insert new entry
        self.ring[self.head] = (now, pattern_id)
        self.head = (self.head + 1) % self.ring_size
        
        # Update counters
        self.counts[pattern_id] += 1
        if pattern_id not in self.first_seen:
            self.first_seen[pattern_id] = now
        self.last_seen[pattern_id] = now
        
        return {
            "pattern": pattern_id,
            "count": self.counts[pattern_id],
            "frequency_hz": self.counts[pattern_id] / (now - self.first_seen[pattern_id]) if now > self.first_seen[pattern_id] else 0,
            "should_synthesize": self.counts[pattern_id] >= 3
        }
    
    def get_hot_patterns(self, threshold=3):
        """Return patterns exceeding threshold. O(n) in pattern count."""
        return {p: c for p, c in self.counts.items() if c >= threshold}
    
    def dump_state(self):
        """Kernel-style state dump for debugging."""
        return {
            "ring_utilization": sum(1 for _, p in self.ring if p) / self.ring_size,
            "unique_patterns": len(self.counts),
            "hot_patterns": self.get_hot_patterns(),
            "total_events": sum(self.counts.values())
        }

_COUNTER = AutosynthPatternCounter()

def record_autosynth(pattern_id: str):
    return _COUNTER.record(pattern_id)