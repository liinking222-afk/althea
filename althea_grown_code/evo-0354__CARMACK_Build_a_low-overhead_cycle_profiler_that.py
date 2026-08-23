import time
from collections import defaultdict

class CycleProfiler:
    __slots__ = ('_buckets', '_start', '_active_op', '_mask', '_shift')
    
    def __init__(self):
        self._buckets = defaultdict(lambda: [0, 0, 0])  # [count, total_tokens, total_ns]
        self._start = 0
        self._active_op = None
        self._mask = 0xFFFFFF  # 16M token max before overflow
        self._shift = 10  # bucket by 1024-token chunks
    
    def start(self, op_name: str, token_estimate: int):
        # Inline hot path: pack token estimate via bit shift for cache-friendly bucketing
        self._active_op = (op_name, token_estimate)
        self._start = time.perf_counter_ns()
    
    def end(self):
        if not self._active_op:
            return
        
        elapsed_ns = time.perf_counter_ns() - self._start
        op_name, tokens = self._active_op
        
        # Integer math only: pack bucket key via bit ops
        bucket_key = (tokens & self._mask) >> self._shift
        key = f"{op_name}:{bucket_key}k"
        
        # Tight loop - no conditionals
        b = self._buckets[key]
        b[0] += 1
        b[1] += tokens
        b[2] += elapsed_ns
        
        self._active_op = None
    
    def get_efficiency(self):
        # tokens/microsecond across all ops - maximize this
        results = []
        for k, (count, total_tok, total_ns) in self._buckets.items():
            if total_ns == 0:
                continue
            us = total_ns / 1000
            efficiency = (total_tok * 1000000) / total_ns  # tok/sec as float
            avg_us = us / count
            results.append((k, count, efficiency, avg_us))
        
        return sorted(results, key=lambda x: -x[2])  # descending by efficiency
    
    def hot_path_report(self) -> str:
        top = self.get_efficiency()[:5]
        return '\n'.join(f"{k}: {eff:.1f}tok/s @{avg:.0f}µs" 
                        for k, cnt, eff, avg in top)

_GLOBAL_PROFILER = CycleProfiler()

def profile_op(name: str, tokens: int):
    _GLOBAL_PROFILER.start(name, tokens)

def end_profile():
    _GLOBAL_PROFILER.end()

def report():
    return _GLOBAL_PROFILER.hot_path_report()