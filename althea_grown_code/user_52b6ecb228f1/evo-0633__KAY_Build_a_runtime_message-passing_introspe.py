import inspect
import sys
from typing import Any, Callable, Dict, Optional
from dataclasses import dataclass, field
from datetime import datetime

@dataclass
class Message:
    sender: str
    receiver: str
    method: str
    payload: Any
    timestamp: float = field(default_factory=lambda: datetime.now().timestamp())

class LiveObject:
    """Kay-style object: responds to messages, can rebind methods at runtime"""
    def __init__(self, name: str):
        self.name = name
        self._methods: Dict[str, Callable] = {}
        self._message_log: list[Message] = []
        self._bindings: Dict[str, 'LiveObject'] = {}
    
    def bind(self, slot: str, target: 'LiveObject') -> None:
        """Late-bind a dependency slot to another live object"""
        self._bindings[slot] = target
    
    def rebind(self, slot: str, new_target: 'LiveObject') -> None:
        """Hot-swap a binding while running"""
        old = self._bindings.get(slot)
        self._bindings[slot] = new_target
        self.send_message(self.name, "rebind", {"slot": slot, "old": old, "new": new_target})
    
    def install_method(self, name: str, func: Callable) -> None:
        """Install or replace a method at runtime"""
        self._methods[name] = func
    
    def send_message(self, receiver: str, method: str, payload: Any) -> Any:
        """Send message to self or bound object"""
        msg = Message(self.name, receiver, method, payload)
        self._message_log.append(msg)
        
        if receiver == self.name and method in self._methods:
            return self._methods[method](payload)
        elif receiver in self._bindings:
            return self._bindings[receiver].receive_message(msg)
        return None
    
    def receive_message(self, msg: Message) -> Any:
        """Receive and handle message"""
        self._message_log.append(msg)
        if msg.method in self._methods:
            return self._methods[msg.method](msg.payload)
        return None
    
    def introspect(self) -> Dict:
        """Return runtime structure snapshot"""
        return {
            "name": self.name,
            "methods": list(self._methods.keys()),
            "bindings": {k: v.name for k, v in self._bindings.items()},
            "messages_sent": len(self._message_log)
        }

class AltheaRuntime:
    """Global registry of live objects with hot-swap capability"""
    _objects: Dict[str, LiveObject] = {}
    
    @classmethod
    def register(cls, obj: LiveObject) -> None:
        cls._objects[obj.name] = obj
    
    @classmethod
    def get(cls, name: str) -> Optional[LiveObject]:
        return cls._objects.get(name)
    
    @classmethod
    def snapshot(cls) -> Dict:
        return {name: obj.introspect() for name, obj in cls._objects.items()}