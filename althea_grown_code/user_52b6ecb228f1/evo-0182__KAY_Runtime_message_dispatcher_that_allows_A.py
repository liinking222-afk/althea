import inspect
import threading
from typing import Callable, Dict, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime

@dataclass
class Message:
    selector: str
    args: tuple
    kwargs: dict
    timestamp: datetime = field(default_factory=datetime.now)

class LiveObject:
    """Kay-style object: late-bound message passing with runtime handler swapping"""
    
    def __init__(self, name: str):
        self.name = name
        self._handlers: Dict[str, Callable] = {}
        self._lock = threading.RLock()
        self._message_history = []
        
    def bind(self, selector: str, handler: Callable) -> 'LiveObject':
        """Late-bind a message handler at runtime"""
        with self._lock:
            self._handlers[selector] = handler
        return self
    
    def unbind(self, selector: str) -> 'LiveObject':
        """Remove a handler at runtime"""
        with self._lock:
            self._handlers.pop(selector, None)
        return self
    
    def send(self, selector: str, *args, **kwargs) -> Any:
        """Send message to object; resolve handler at call-time"""
        msg = Message(selector, args, kwargs)
        
        with self._lock:
            handler = self._handlers.get(selector)
            self._message_history.append(msg)
            
        if handler is None:
            return self._does_not_understand(msg)
        
        sig = inspect.signature(handler)
        if 'self' in sig.parameters:
            return handler(self, *args, **kwargs)
        return handler(*args, **kwargs)
    
    def _does_not_understand(self, msg: Message) -> Any:
        """Default behavior for unknown messages"""
        raise AttributeError(f"{self.name} does not understand '{msg.selector}'")
    
    def introspect(self) -> Dict[str, Any]:
        """Runtime reflection of current capabilities"""
        with self._lock:
            return {
                'name': self.name,
                'handlers': list(self._handlers.keys()),
                'message_count': len(self._message_history)
            }

class AltheaLiveRuntime:
    """Global registry for hot-swappable Althea subsystems"""
    
    _objects: Dict[str, LiveObject] = {}
    _lock = threading.RLock()
    
    @classmethod
    def register(cls, obj: LiveObject) -> None:
        with cls._lock:
            cls._objects[obj.name] = obj
    
    @classmethod
    def get(cls, name: str) -> Optional[LiveObject]:
        with cls._lock:
            return cls._objects.get(name)
    
    @classmethod
    def rebind_live(cls, obj_name: str, selector: str, new_handler: Callable) -> bool:
        """Hot-swap a handler in a running object"""
        obj = cls.get(obj_name)
        if obj:
            obj.bind(selector, new_handler)
            return True
        return False