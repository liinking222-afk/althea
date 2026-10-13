import time
import tracemalloc
from functools import wraps
from collections import defaultdict
from datetime import datetime
import json

class ResourceProfiler:
    def __init__(self):
        self.profiles = defaultdict(lambda: {
            'calls': 0,
            'total_time_ms': 0,
            'total_tokens': 0,
            'total_memory_kb': 0,
            'avg_time_ms': 0,
            'avg_tokens': 0,
            'avg_memory_kb': 0
        })
    
    def profile(self, module_name, token_estimate=0):
        def decorator(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                tracemalloc.start()
                start_time = time.perf_counter()
                start_mem = tracemalloc.get_traced_memory()[0]
                
                result = func(*args, **kwargs)
                
                end_time = time.perf_counter()
                end_mem = tracemalloc.get_traced_memory()[0]
                tracemalloc.stop()
                
                elapsed_ms = (end_time - start_time) * 1000
                mem_delta_kb = (end_mem - start_mem) / 1024
                
                profile = self.profiles[module_name]
                profile['calls'] += 1
                profile['total_time_ms'] += elapsed_ms
                profile['total_tokens'] += token_estimate
                profile['total_memory_kb'] += mem_delta_kb
                profile['avg_time_ms'] = profile['total_time_ms'] / profile['calls']
                profile['avg_tokens'] = profile['total_tokens'] / profile['calls']
                profile['avg_memory_kb'] = profile['total_memory_kb'] / profile['calls']
                
                return result
            return wrapper
        return decorator
    
    def get_report(self, sort_by='avg_time_ms'):
        sorted_profiles = sorted(
            self.profiles.items(),
            key=lambda x: x[1][sort_by],
            reverse=True
        )
        return {
            'timestamp': datetime.utcnow().isoformat(),
            'modules': dict(sorted_profiles)
        }
    
    def get_budget_status(self, token_budget=200000):
        total_tokens = sum(p['total_tokens'] for p in self.profiles.values())
        return {
            'used': total_tokens,
            'budget': token_budget,
            'remaining': token_budget - total_tokens,
            'utilization': total_tokens / token_budget
        }

profiler = ResourceProfiler()