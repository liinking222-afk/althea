#!/usr/bin/env python3
"""Resource profiler for Althea modules - make every token count."""

import json
import time
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, Any

class ResourceProfiler:
    def __init__(self, profile_dir: Path = Path.home() / ".althea" / "profiles"):
        self.profile_dir = profile_dir
        self.profile_dir.mkdir(parents=True, exist_ok=True)
        self.session_start = time.time()
        
    def start_profile(self, module: str) -> Dict[str, Any]:
        """Begin profiling a module execution."""
        return {
            "module": module,
            "start_time": time.time(),
            "start_memory": self._get_memory_usage()
        }
    
    def end_profile(self, context: Dict[str, Any], tokens_used: int = 0, 
                    success: bool = True) -> None:
        """Complete profile and persist efficiency metrics."""
        duration = time.time() - context["start_time"]
        memory_delta = self._get_memory_usage() - context["start_memory"]
        
        profile = {
            "module": context["module"],
            "timestamp": datetime.now().isoformat(),
            "duration_ms": round(duration * 1000, 2),
            "memory_delta_kb": round(memory_delta / 1024, 2),
            "tokens_used": tokens_used,
            "efficiency": round(1000 / (tokens_used + 1), 4),  # ops per token
            "success": success
        }
        
        self._persist(profile)
        self._emit_metrics(profile)
    
    def _get_memory_usage(self) -> int:
        """Get current process memory in bytes."""
        try:
            import resource
            return resource.getrusage(resource.RUSAGE_SELF).ru_maxrss * 1024
        except:
            return 0
    
    def _persist(self, profile: Dict[str, Any]) -> None:
        """Append profile to JSONL log."""
        log_file = self.profile_dir / f"profiles-{datetime.now().strftime('%Y%m')}.jsonl"
        with open(log_file, "a") as f:
            f.write(json.dumps(profile) + "\n")
    
    def _emit_metrics(self, profile: Dict[str, Any]) -> None:
        """Emit compact metrics to stderr for pipeline monitoring."""
        sys.stderr.write(f"[PROFILE] {profile['module']}: "
                        f"{profile['duration_ms']}ms, "
                        f"{profile['tokens_used']}tok, "
                        f"eff={profile['efficiency']}\n")
    
    def report_top_inefficient(self, n: int = 5) -> None:
        """Report modules with worst token efficiency."""
        profiles = self._load_recent(limit=1000)
        sorted_profiles = sorted(profiles, key=lambda p: p.get("efficiency", 999))
        
        print(f"Top {n} least efficient modules (by tokens):")
        for p in sorted_profiles[:n]:
            print(f"  {p['module']}: {p['tokens_used']} tokens, "
                  f"{p['duration_ms']}ms, eff={p['efficiency']}")
    
    def _load_recent(self, limit: int = 1000) -> list:
        """Load recent profile records."""
        profiles = []
        for log_file in sorted(self.profile_dir.glob("profiles-*.jsonl"), reverse=True):
            with open(log_file) as f:
                for line in f:
                    profiles.append(json.loads(line))
                    if len(profiles) >= limit:
                        return profiles
        return profiles

if __name__ == "__main__":
    profiler = ResourceProfiler()
    profiler.report_top_inefficient()