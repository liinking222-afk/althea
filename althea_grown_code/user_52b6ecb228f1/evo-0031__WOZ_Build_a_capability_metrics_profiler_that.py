#!/usr/bin/env python3
import time
import json
from collections import defaultdict
from pathlib import Path

class CapabilityProfiler:
    """WOZ-inspired: measure what you optimize. Every token counts."""
    
    def __init__(self, trace_path="./memory/capability_profile.jsonl"):
        self.trace_path = Path(trace_path)
        self.trace_path.parent.mkdir(parents=True, exist_ok=True)
        self.active_spans = {}
        self.stats = defaultdict(lambda: {"calls": 0, "total_ms": 0, "total_tokens": 0})
    
    def start_span(self, capability_name, estimated_tokens=0):
        """Begin measuring a capability invocation."""
        span_id = f"{capability_name}:{time.time_ns()}"
        self.active_spans[span_id] = {
            "name": capability_name,
            "start": time.perf_counter(),
            "est_tokens": estimated_tokens
        }
        return span_id
    
    def end_span(self, span_id, actual_tokens=None):
        """Complete measurement and persist trace."""
        if span_id not in self.active_spans:
            return
        
        span = self.active_spans.pop(span_id)
        elapsed_ms = (time.perf_counter() - span["start"]) * 1000
        tokens = actual_tokens or span["est_tokens"]
        
        name = span["name"]
        self.stats[name]["calls"] += 1
        self.stats[name]["total_ms"] += elapsed_ms
        self.stats[name]["total_tokens"] += tokens
        
        record = {
            "ts": time.time(),
            "capability": name,
            "duration_ms": round(elapsed_ms, 2),
            "tokens": tokens,
            "efficiency": round(tokens / elapsed_ms, 2) if elapsed_ms > 0 else 0
        }
        
        with open(self.trace_path, "a") as f:
            f.write(json.dumps(record) + "\n")
    
    def report(self):
        """Generate WOZ-style constraint analysis: cost per capability."""
        lines = ["CAPABILITY PROFILE (tokens/ms efficiency):"]
        for name, data in sorted(self.stats.items(), 
                                 key=lambda x: x[1]["total_tokens"], 
                                 reverse=True):
            avg_ms = data["total_ms"] / data["calls"]
            avg_tok = data["total_tokens"] / data["calls"]
            lines.append(f"  {name:30} {data['calls']:4}x  "
                        f"{avg_tok:6.0f}tok  {avg_ms:6.1f}ms  "
                        f"({avg_tok/avg_ms if avg_ms > 0 else 0:.1f} tok/ms)")
        return "\n".join(lines)

if __name__ == "__main__":
    profiler = CapabilityProfiler()
    print(profiler.report())