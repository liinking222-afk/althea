import asyncio
from typing import Callable, Any, Dict, Set
from dataclasses import dataclass, field
from datetime import datetime

@dataclass
class Message:
    source: str
    event: str
    payload: Any
    timestamp: float = field(default_factory=lambda: datetime.now().timestamp())

class ReflectionBus:
    """Late-binding message bus for runtime subsystem coordination"""
    
    def __init__(self):
        self._subscribers: Dict[str, Set[Callable]] = {}
        self._message_history: list[Message] = []
        self._max_history = 100
        
    def send(self, source: str, event: str, payload: Any = None):
        """Send message to all subscribers of this event pattern"""
        msg = Message(source=source, event=event, payload=payload)
        self._message_history.append(msg)
        if len(self._message_history) > self._max_history:
            self._message_history.pop(0)
        
        # Exact match subscribers
        for handler in self._subscribers.get(event, set()):
            try:
                handler(msg)
            except Exception as e:
                self.send("reflection_bus", "handler_error", 
                         {"event": event, "error": str(e)})
        
        # Wildcard subscribers
        for handler in self._subscribers.get("*", set()):
            try:
                handler(msg)
            except Exception as e:
                pass
    
    def subscribe(self, event: str, handler: Callable[[Message], None]):
        """Subscribe to events at runtime"""
        if event not in self._subscribers:
            self._subscribers[event] = set()
        self._subscribers[event].add(handler)
        return lambda: self._subscribers[event].discard(handler)
    
    def inspect(self) -> Dict[str, Any]:
        """Reflect on current bus state"""
        return {
            "active_subscriptions": {k: len(v) for k, v in self._subscribers.items()},
            "recent_messages": self._message_history[-10:],
            "total_subscribers": sum(len(v) for v in self._subscribers.values())
        }
    
    def modify_at_runtime(self, new_max_history: int = None):
        """Demonstrate runtime malleability"""
        if new_max_history:
            self._max_history = new_max_history
            self.send("reflection_bus", "configuration_changed", 
                     {"max_history": new_max_history})

# Global singleton instance
REFLECTION_BUS = ReflectionBus()