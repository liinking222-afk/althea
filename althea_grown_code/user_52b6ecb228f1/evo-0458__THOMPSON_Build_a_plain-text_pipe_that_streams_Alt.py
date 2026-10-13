#!/usr/bin/env python3
import json
import sys
import time
from datetime import datetime
from collections import deque

class AltheaStatePipe:
    def __init__(self, buffer_size=100):
        self.states = deque(maxlen=buffer_size)
        self.start_time = time.time()
    
    def emit(self, event_type, module, data=None):
        """Emit a state transition as NDJSON to stdout"""
        record = {
            "t": time.time() - self.start_time,
            "iso": datetime.utcnow().isoformat() + "Z",
            "type": event_type,
            "module": module,
            "data": data or {}
        }
        self.states.append(record)
        print(json.dumps(record), flush=True)
        return record
    
    def filter(self, predicate):
        """Filter records (composable)"""
        for state in self.states:
            if predicate(state):
                print(json.dumps(state), flush=True)
    
    def replay(self):
        """Replay buffered states to stdout"""
        for state in self.states:
            print(json.dumps(state), flush=True)

# Singleton instance
_pipe = AltheaStatePipe()

def emit_state(event_type, module, **kwargs):
    return _pipe.emit(event_type, module, kwargs)

def emit_module_call(module, inputs):
    return emit_state("CALL", module, inputs=inputs)

def emit_module_return(module, outputs, duration):
    return emit_state("RETURN", module, outputs=outputs, duration_ms=duration*1000)

def emit_evolution(version, description):
    return emit_state("EVO", "core", version=version, desc=description)

def emit_growth(pattern, mode):
    return emit_state("GROWTH", pattern, mode=mode)

if __name__ == "__main__":
    # Demo: pipe to jq, grep, awk, etc.
    emit_module_call("perception", {"query": "test"})
    time.sleep(0.01)
    emit_module_return("perception", {"response": "ok"}, 0.01)
    emit_evolution("1.41.7", "state pipe")
    emit_growth("threshold-oscillation", "perception")