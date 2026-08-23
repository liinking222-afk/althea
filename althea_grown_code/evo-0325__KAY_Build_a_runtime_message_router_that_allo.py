#!/usr/bin/env python3
import json
from typing import Callable, Dict, List, Any
from collections import defaultdict
from datetime import datetime

class MessageBus:
    def __init__(self):
        self.handlers: Dict[str, List[Callable]] = defaultdict(list)
        self.message_log: List[Dict[str, Any]] = []
        
    def subscribe(self, message_type: str, handler: Callable) -> str:
        """Late-bind a handler to a message type at runtime"""
        handler_id = f"{message_type}:{id(handler)}"
        self.handlers[message_type].append(handler)
        return handler_id
    
    def unsubscribe(self, message_type: str, handler: Callable):
        """Remove handler binding at runtime"""
        if handler in self.handlers[message_type]:
            self.handlers[message_type].remove(handler)
    
    def send(self, message_type: str, payload: Any) -> List[Any]:
        """Pass message to all subscribed handlers"""
        timestamp = datetime.utcnow().isoformat()
        msg = {"type": message_type, "payload": payload, "ts": timestamp}
        self.message_log.append(msg)
        
        results = []
        for handler in self.handlers[message_type]:
            try:
                result = handler(payload)
                results.append(result)
            except Exception as e:
                results.append({"error": str(e), "handler": handler.__name__})
        return results
    
    def introspect(self) -> Dict[str, int]:
        """Runtime reflection of current message topology"""
        return {msg_type: len(handlers) for msg_type, handlers in self.handlers.items()}
    
    def replay(self, message_type: str = None):
        """Replay logged messages through current handler configuration"""
        messages = [m for m in self.message_log if message_type is None or m["type"] == message_type]
        for msg in messages:
            self.send(msg["type"], msg["payload"])

# Global runtime-mutable message bus
ALTHEA_BUS = MessageBus()

# Example: Memory deduplication subscribes at runtime
def dedup_handler(payload):
    if payload.get("consecutive_duplicate"):
        return {"action": "collapse", "original": payload["hash"]}
    return {"action": "store"}

ALTHEA_BUS.subscribe("memory:write", dedup_handler)

# Example: Coherence monitor subscribes at runtime
def coherence_monitor(payload):
    return {"coherence_delta": 0.01, "trigger": payload.get("type")}

ALTHEA_BUS.subscribe("memory:write", coherence_monitor)