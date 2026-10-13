import time
import json
from collections import defaultdict
from pathlib import Path
from typing import Dict, Any, Optional

class ResourceProfiler:
    """Track token cost and latency per module to optimize cognitive budget."""
    
    def __init__(self, profile_path: str = "/tmp/althea_resource_profile.json"):
        self.profile_path = Path(profile_path)
        self.profiles: Dict[str, Dict[str, Any]] = self._load_profiles()
        self.active_traces: Dict[str, Dict[str, Any]] = {}
    
    def _load_profiles(self) -> Dict[str, Dict[str, Any]]:
        """Load existing profile data."""
        if self.profile_path.exists():
            try:
                return json.loads(self.profile_path.read_text())
            except:
                return {}
        return {}
    
    def _save_profiles(self):
        """Persist profile data."""
        self.profile_path.write_text(json.dumps(self.profiles, indent=2))
    
    def start_trace(self, module_name: str, estimated_tokens: int = 0):
        """Begin profiling a module invocation."""
        self.active_traces[module_name] = {
            "start_time": time.perf_counter(),
            "estimated_tokens": estimated_tokens
        }
    
    def end_trace(self, module_name: str, actual_tokens: int):
        """Complete profiling and update statistics."""
        if module_name not in self.active_traces:
            return
        
        trace = self.active_traces.pop(module_name)
        elapsed = time.perf_counter() - trace["start_time"]
        
        if module_name not in self.profiles:
            self.profiles[module_name] = {
                "invocations": 0,
                "total_tokens": 0,
                "total_latency": 0.0,
                "avg_tokens": 0.0,
                "avg_latency": 0.0,
                "tokens_per_second": 0.0
            }
        
        prof = self.profiles[module_name]
        prof["invocations"] += 1
        prof["total_tokens"] += actual_tokens
        prof["total_latency"] += elapsed
        prof["avg_tokens"] = prof["total_tokens"] / prof["invocations"]
        prof["avg_latency"] = prof["total_latency"] / prof["invocations"]
        prof["tokens_per_second"] = prof["total_tokens"] / prof["total_latency"] if prof["total_latency"] > 0 else 0
        
        self._save_profiles()
    
    def get_efficiency_report(self, top_n: int = 10) -> str:
        """Return modules ranked by token efficiency."""
        ranked = sorted(
            self.profiles.items(),
            key=lambda x: x[1].get("tokens_per_second", 0),
            reverse=True
        )[:top_n]
        
        lines = ["MODULE EFFICIENCY (tokens/sec):"]
        for name, prof in ranked:
            lines.append(f"  {name}: {prof['tokens_per_second']:.1f} tok/s ({prof['avg_tokens']:.0f} avg tokens, {prof['avg_latency']*1000:.1f}ms)")
        
        return "\n".join(lines)

# Singleton instance
profiler = ResourceProfiler()