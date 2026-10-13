import json
from typing import Any, Callable, Dict, List, Optional
from dataclasses import dataclass, asdict
from datetime import datetime
import threading

@dataclass
class Message:
    type: str
    payload: Any
    sender: str
    timestamp: str = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.utcnow().isoformat()
    
    def to_dict(self):
        return asdict(self)

class MessageBus:
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._handlers: Dict[str, List[Callable]] = {}
                    cls._instance._history: List[Message] = []
                    cls._instance._max_history = 1000
        return cls._instance
    
    def subscribe(self, message_type: str, handler: Callable[[Message], None]):
        """Register a handler for a message type at runtime"""
        if message_type not in self._handlers:
            self._handlers[message_type] = []
        self._handlers[message_type].append(handler)
        return lambda: self.unsubscribe(message_type, handler)
    
    def unsubscribe(self, message_type: str, handler: Callable):
        """Remove a handler while system is running"""
        if message_type in self._handlers:
            self._handlers[message_type] = [h for h in self._handlers[message_type] if h != handler]
    
    def publish(self, message_type: str, payload: Any, sender: str = "unknown"):
        """Broadcast message to all registered handlers"""
        msg = Message(type=message_type, payload=payload, sender=sender)
        self._history.append(msg)
        if len(self._history) > self._max_history:
            self._history.pop(0)
        
        for handler in self._handlers.get(message_type, []):
            try:
                handler(msg)
            except Exception as e:
                print(f"Handler error for {message_type}: {e}")
    
    def list_subscriptions(self) -> Dict[str, int]:
        """Introspect current message routing"""
        return {msg_type: len(handlers) for msg_type, handlers in self._handlers.items()}
    
    def replay(self, message_type: Optional[str] = None, limit: int = 100):
        """Access message history for late-binding consumers"""
        filtered = [m for m in self._history if message_type is None or m.type == message_type]
        return filtered[-limit:]

bus = MessageBus()