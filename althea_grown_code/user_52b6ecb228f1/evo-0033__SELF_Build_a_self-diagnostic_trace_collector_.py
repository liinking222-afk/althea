import json
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List

class CreationTraceCollector:
    """Captures metadata about Althea's self-modification events."""
    
    def __init__(self, trace_file: str = "/tmp/althea_creation_traces.jsonl"):
        self.trace_file = Path(trace_file)
        self.current_trace: Dict[str, Any] = {}
        
    def start_trace(self, archetype: str, context: Dict[str, Any]) -> None:
        """Begin recording a creation event."""
        self.current_trace = {
            "trace_id": f"{int(time.time() * 1000000)}",
            "timestamp": datetime.utcnow().isoformat(),
            "archetype": archetype,
            "context_snapshot": context,
            "start_time": time.time()
        }
    
    def record_decision(self, key: str, value: Any, rationale: str = "") -> None:
        """Log a decision point during module creation."""
        if "decisions" not in self.current_trace:
            self.current_trace["decisions"] = []
        self.current_trace["decisions"].append({
            "key": key,
            "value": value,
            "rationale": rationale,
            "timestamp": time.time() - self.current_trace["start_time"]
        })
    
    def complete_trace(self, module_info: Dict[str, Any]) -> None:
        """Finalize and persist the trace."""
        self.current_trace.update({
            "module": module_info,
            "duration": time.time() - self.current_trace["start_time"],
            "completion_timestamp": datetime.utcnow().isoformat()
        })
        
        with open(self.trace_file, "a") as f:
            f.write(json.dumps(self.current_trace) + "\n")
        
        self.current_trace = {}
    
    def analyze_patterns(self, last_n: int = 20) -> Dict[str, Any]:
        """Identify patterns in recent creation events."""
        if not self.trace_file.exists():
            return {"error": "No traces found"}
        
        traces = []
        with open(self.trace_file, "r") as f:
            for line in f:
                traces.append(json.loads(line))
        
        recent = traces[-last_n:] if len(traces) > last_n else traces
        
        return {
            "total_traces": len(traces),
            "avg_duration": sum(t["duration"] for t in recent) / len(recent),
            "archetype_distribution": self._count_field(recent, "archetype"),
            "common_decision_keys": self._extract_decision_keys(recent)
        }
    
    def _count_field(self, traces: List[Dict], field: str) -> Dict[str, int]:
        counts = {}
        for t in traces:
            val = t.get(field, "unknown")
            counts[val] = counts.get(val, 0) + 1
        return counts
    
    def _extract_decision_keys(self, traces: List[Dict]) -> List[str]:
        keys = set()
        for t in traces:
            for decision in t.get("decisions", []):
                keys.add(decision["key"])
        return sorted(list(keys))