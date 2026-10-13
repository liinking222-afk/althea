#!/usr/bin/env python3
import sys
import json
import time
from datetime import datetime
from pathlib import Path

class StreamLogger:
    """Thompson-style: emit plain text, one event per line, pipe-friendly"""
    
    def __init__(self, stream=sys.stdout):
        self.stream = stream
        self.stream.reconfigure(line_buffering=True)
    
    def log_event(self, event_type, data):
        """Emit single-line JSON event to stdout"""
        event = {
            "ts": datetime.utcnow().isoformat(),
            "type": event_type,
            "data": data
        }
        print(json.dumps(event, separators=(',', ':')), file=self.stream, flush=True)
    
    def log_pattern(self, pattern, source, confidence=1.0):
        """Log AUTOSYNTH pattern detection"""
        self.log_event("pattern", {
            "pattern": pattern,
            "source": source,
            "conf": confidence
        })
    
    def log_synthesis(self, module_path, trigger):
        """Log module synthesis event"""
        self.log_event("synth", {
            "module": module_path,
            "trigger": trigger
        })
    
    def log_evolution(self, evo_id, component, version_from, version_to):
        """Log evolution cycle"""
        self.log_event("evo", {
            "id": evo_id,
            "component": component,
            "from": version_from,
            "to": version_to
        })

def grep_patterns(pattern_filter=None):
    """Read from stdin, filter, emit matching lines - classic UNIX filter"""
    for line in sys.stdin:
        try:
            event = json.loads(line.strip())
            if pattern_filter is None or pattern_filter in event.get("data", {}).get("pattern", ""):
                print(line.strip(), flush=True)
        except:
            continue

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "grep":
        pattern = sys.argv[2] if len(sys.argv) > 2 else None
        grep_patterns(pattern)
    else:
        logger = StreamLogger()
        logger.log_pattern("linguistic-bridge", "dialogue", 0.92)
        logger.log_pattern("data-visualization", "dialogue", 0.88)
        logger.log_synthesis("/autonomous-linguistic-bridge-4577", "pattern_threshold")