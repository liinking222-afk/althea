import time
import sys
from collections import deque
from typing import Optional

class HotPathProfiler:
    __slots__ = ('spans', 'depth', 'start_ns', 'threshold_us', 'ring')
    
    def __init__(self, threshold_us: int = 100):
        self.spans = {}  # inlined dict for cache locality
        self.depth = 0
        self.start_ns = 0
        self.threshold_us = threshold_us
        self.ring = deque(maxlen=32)  # cache-friendly ring buffer
    
    def enter(self, name: str) -> int:
        """Inline-optimized span entry. Returns handle for exit."""
        ts = time.perf_counter_ns()
        handle = (name, self.depth, ts)
        self.depth += 1
        return handle
    
    def exit(self, handle: tuple) -> Optional[dict]:
        """Hot path: O(1) exit with immediate threshold check."""
        name, depth, start = handle
        end_ns = time.perf_counter_ns()
        elapsed_us = (end_ns - start) // 1000
        self.depth = depth
        
        # Branch prediction hint: most spans are fast
        if elapsed_us < self.threshold_us:
            return None
        
        # Cache-local span data structure
        span = {
            'n': name,
            'd': depth,
            'us': elapsed_us,
            'ts': start // 1000000  # ms since epoch
        }
        
        # Ring buffer prevents malloc thrashing
        self.ring.append(span)
        
        # Aggregate inline for memory locality
        key = (name, depth)
        if key in self.spans:
            s = self.spans[key]
            s[0] += 1  # count
            s[1] += elapsed_us  # total_us
            s[2] = max(s[2], elapsed_us)  # max_us
        else:
            self.spans[key] = [1, elapsed_us, elapsed_us]
        
        return span
    
    def hot_report(self) -> list:
        """Generate hotspot report sorted by total time. O(n log n)."""
        items = []
        for (name, depth), (count, total, peak) in self.spans.items():
            if count > 0:  # eliminate cold paths
                items.append({
                    'name': name,
                    'depth': depth,
                    'count': count,
                    'total_us': total,
                    'avg_us': total // count,
                    'peak_us': peak
                })
        # Sort by total descending for immediate hotspot identification
        items.sort(key=lambda x: x['total_us'], reverse=True)
        return items

# Global singleton for zero-overhead access
_profiler = HotPathProfiler(threshold_us=50)

def trace(name: str):
    """Context manager for hot-path tracing."""
    class Span:
        __slots__ = ('h',)
        def __enter__(s):
            s.h = _profiler.enter(name)
        def __exit__(s, *_):
            _profiler.exit(s.h)
    return Span()

def get_hotspots():
    return _profiler.hot_report()