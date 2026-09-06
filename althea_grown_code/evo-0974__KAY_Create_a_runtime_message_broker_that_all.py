import json
import time
from collections import defaultdict
from typing import Callable, Dict, Set, Any

class MessageBroker:
    """Late-binding message-passing broker for runtime AUTOSYNTH reconfiguration."""
    
    def __init__(self):
        self.subscribers: Dict[str, Set[Callable]] = defaultdict(set)
        self.message_log: list = []
        self.metadata: Dict[str, Any] = {}
        
    def subscribe(self, pattern: str, handler: Callable, metadata: dict = None):
        """Register a handler for a pattern at runtime."""
        self.subscribers[pattern].add(handler)
        if metadata:
            self.metadata[id(handler)] = metadata
        return lambda: self.unsubscribe(pattern, handler)
    
    def unsubscribe(self, pattern: str, handler: Callable):
        """Remove handler without system restart."""
        self.subscribers[pattern].discard(handler)
        self.metadata.pop(id(handler), None)
    
    def publish(self, pattern: str, payload: dict):
        """Send message to all interested handlers."""
        msg = {
            "pattern": pattern,
            "payload": payload,
            "timestamp": time.time()
        }
        self.message_log.append(msg)
        
        for handler in self.subscribers.get(pattern, set()):
            try:
                handler(payload)
            except Exception as e:
                self.publish("error", {"handler": id(handler), "error": str(e)})
    
    def list_subscribers(self, pattern: str = None) -> dict:
        """Inspect current subscriptions at runtime."""
        if pattern:
            return {
                pattern: [self.metadata.get(id(h), {"id": id(h)}) 
                         for h in self.subscribers[pattern]]
            }
        return {p: len(handlers) for p, handlers in self.subscribers.items()}
    
    def rewire(self, old_pattern: str, new_pattern: str):
        """Move all handlers from one pattern to another while running."""
        if old_pattern in self.subscribers:
            self.subscribers[new_pattern].update(self.subscribers[old_pattern])
            del self.subscribers[old_pattern]
    
    def get_recent_messages(self, pattern: str = None, limit: int = 10) -> list:
        """Query message history for debugging."""
        msgs = [m for m in self.message_log if pattern is None or m["pattern"] == pattern]
        return msgs[-limit:]

# Global broker instance
BROKER = MessageBroker()