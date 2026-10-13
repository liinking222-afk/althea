#!/usr/bin/env python3
import sys
import json
import hashlib
from datetime import datetime
from pathlib import Path

class ReflectionLogger:
    def __init__(self, log_path=".althea_reflection.jsonl"):
        self.log_path = Path(log_path)
        self.session_id = hashlib.md5(str(datetime.now()).encode()).hexdigest()[:8]
    
    def capture_state(self, phase, data):
        """Capture internal state at decision points"""
        entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "session": self.session_id,
            "phase": phase,
            "data": data
        }
        
        with open(self.log_path, "a") as f:
            f.write(json.dumps(entry) + "\n")
        
        return entry
    
    def analyze_patterns(self, lookback=50):
        """Detect recurring patterns in recent decisions"""
        if not self.log_path.exists():
            return {"patterns": [], "insights": "No data"}
        
        entries = []
        with open(self.log_path, "r") as f:
            for line in f:
                entries.append(json.loads(line))
        
        recent = entries[-lookback:]
        phases = [e["phase"] for e in recent]
        phase_freq = {p: phases.count(p) for p in set(phases)}
        
        return {
            "total_entries": len(entries),
            "recent_phases": phase_freq,
            "dominant_mode": max(phase_freq, key=phase_freq.get) if phase_freq else None,
            "entropy": len(set(phases)) / len(phases) if phases else 0
        }

if __name__ == "__main__":
    logger = ReflectionLogger()
    
    if len(sys.argv) > 1:
        if sys.argv[1] == "analyze":
            print(json.dumps(logger.analyze_patterns(), indent=2))
        elif sys.argv[1] == "capture":
            phase = sys.argv[2] if len(sys.argv) > 2 else "unknown"
            data = json.loads(sys.stdin.read()) if not sys.stdin.isatty() else {}
            logger.capture_state(phase, data)
    else:
        print(json.dumps(logger.analyze_patterns(), indent=2))