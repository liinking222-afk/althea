import inspect
import threading
from typing import Any, Callable, Dict, Optional
from dataclasses import dataclass, field
from datetime import datetime

@dataclass
class MessageHandler:
    func: Callable
    version: str
    loaded_at: datetime = field(default_factory=datetime.now)
    call_count: int = 0

class RuntimeDispatcher:
    def __init__(self):
        self._handlers: Dict[str, MessageHandler] = {}
        self._lock = threading.RLock()
        self._fallback: Optional[Callable] = None
    
    def register(self, message_type: str, handler: Callable, version: str = "1.0.0"):
        with self._lock:
            self._handlers[message_type] = MessageHandler(handler, version)
        return self
    
    def hot_swap(self, message_type: str, new_handler: Callable, version: str):
        with self._lock:
            if message_type in self._handlers:
                old = self._handlers[message_type]
                self._handlers[message_type] = MessageHandler(
                    new_handler, version, call_count=old.call_count
                )
                return old.func
        return None
    
    def send(self, message_type: str, *args, **kwargs) -> Any:
        with self._lock:
            if message_type in self._handlers:
                handler = self._handlers[message_type]
                handler.call_count += 1
                return handler.func(*args, **kwargs)
            elif self._fallback:
                return self._fallback(message_type, *args, **kwargs)
            raise ValueError(f"No handler for message: {message_type}")
    
    def introspect(self, message_type: str) -> Optional[Dict[str, Any]]:
        with self._lock:
            if message_type in self._handlers:
                h = self._handlers[message_type]
                return {
                    "version": h.version,
                    "signature": str(inspect.signature(h.func)),
                    "loaded_at": h.loaded_at.isoformat(),
                    "call_count": h.call_count
                }
        return None
    
    def set_fallback(self, handler: Callable):
        with self._lock:
            self._fallback = handler
    
    def list_messages(self) -> list[str]:
        with self._lock:
            return list(self._handlers.keys())

_global_dispatcher = RuntimeDispatcher()

def dispatch(message_type: str, *args, **kwargs):
    return _global_dispatcher.send(message_type, *args, **kwargs)

def register_handler(message_type: str, version: str = "1.0.0"):
    def decorator(func: Callable):
        _global_dispatcher.register(message_type, func, version)
        return func
    return decorator