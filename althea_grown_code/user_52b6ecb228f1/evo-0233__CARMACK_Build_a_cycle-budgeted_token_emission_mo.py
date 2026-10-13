import time
from collections import deque
from dataclasses import dataclass

@dataclass
class CycleMetrics:
    tokens: int
    nanos: int
    semantic_weight: float  # 0.0=meta, 1.0=executable
    
    @property
    def cycles_per_semantic(self) -> float:
        # Fast path: zero semantic = infinite waste
        return float('inf') if self.semantic_weight < 1e-9 else (self.tokens / self.semantic_weight)

class HotPathMonitor:
    __slots__ = ('_window', '_budget', '_t0', '_token_count', '_cumulative_semantic')
    
    def __init__(self, token_budget: int = 200000, window_size: int = 16):
        self._window = deque(maxlen=window_size)  # Ring buffer for cache locality
        self._budget = token_budget
        self._t0 = time.perf_counter_ns()
        self._token_count = 0
        self._cumulative_semantic = 0.0
    
    def emit(self, token_delta: int, semantic_weight: float) -> bool:
        """Returns True if emission is allowed, False if budget exceeded."""
        # Inline hot path: increment first, branch prediction optimized
        self._token_count += token_delta
        self._cumulative_semantic += semantic_weight
        
        # Fast reject: hard budget
        if self._token_count > self._budget:
            return False
        
        # Record metric (amortized over window)
        nanos = time.perf_counter_ns() - self._t0
        metric = CycleMetrics(token_delta, nanos, semantic_weight)
        self._window.append(metric)
        
        # Window threshold: average efficiency check
        if len(self._window) >= 8:  # Wait for statistical power
            avg_cps = sum(m.cycles_per_semantic for m in self._window) / len(self._window)
            # Kill path if average waste exceeds 1000 tokens per semantic unit
            if avg_cps > 1000.0:
                return False
        
        return True
    
    def current_efficiency(self) -> float:
        """Tokens per unit semantic content (lower is better)."""
        return self._token_count / max(self._cumulative_semantic, 1e-9)
    
    def remaining_budget(self) -> int:
        return max(0, self._budget - self._token_count)

# Global singleton for sub-millisecond lookups
_monitor = HotPathMonitor()

def should_emit(tokens: int, is_executable: bool) -> bool:
    """Inline-optimized emission gate. Call before every output."""
    return _monitor.emit(tokens, 1.0 if is_executable else 0.1)

def get_efficiency() -> float:
    return _monitor.current_efficiency()