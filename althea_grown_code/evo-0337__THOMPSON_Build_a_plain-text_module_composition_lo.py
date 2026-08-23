#!/usr/bin/env env python3
import json
import sys
from datetime import datetime
from typing import Any, Dict, Optional

class StreamLogger:
    """Emits module interactions as line-delimited JSON to stdout."""
    
    def __init__(self, stream=sys.stdout):
        self.stream = stream
    
    def log(self, event_type: str, module: str, data: Dict[str, Any], 
            metadata: Optional[Dict[str, Any]] = None):
        """Emit a single event as one line of JSON."""
        event = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "type": event_type,
            "module": module,
            "data": data
        }
        if metadata:
            event["meta"] = metadata
        
        print(json.dumps(event, separators=(',', ':')), file=self.stream, flush=True)
    
    def module_call(self, caller: str, callee: str, args: Dict[str, Any]):
        """Log a module-to-module call."""
        self.log("call", caller, {"target": callee, "args": args})
    
    def module_return(self, module: str, value: Any, duration_ms: float):
        """Log a module return with timing."""
        self.log("return", module, {"value": value}, {"duration_ms": duration_ms})
    
    def module_error(self, module: str, error: str, context: Dict[str, Any]):
        """Log a module error."""
        self.log("error", module, {"error": error, "context": context})
    
    def state_change(self, module: str, old_state: str, new_state: str):
        """Log state transitions."""
        self.log("state", module, {"from": old_state, "to": new_state})


if __name__ == "__main__":
    logger = StreamLogger()
    
    logger.module_call("perception", "memory", {"query": "recent_patterns"})
    logger.module_return("memory", {"count": 42}, 15.3)
    logger.state_change("core", "idle", "processing")
    logger.module_error("synthesis", "timeout", {"input_size": 9001})