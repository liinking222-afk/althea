#!/usr/bin/env python3
import inspect
from typing import Any, Callable, Dict, Optional

class MessagePassingObject:
    """Late-bound object that responds to messages at runtime."""
    
    def __init__(self, name: str):
        self.name = name
        self._methods: Dict[str, Callable] = {}
        self._state: Dict[str, Any] = {}
        self._message_log = []
    
    def bind_method(self, message: str, handler: Callable):
        """Late-bind a method at runtime."""
        self._methods[message] = handler
        return self
    
    def unbind_method(self, message: str):
        """Remove a method binding."""
        self._methods.pop(message, None)
        return self
    
    def send(self, message: str, *args, **kwargs) -> Any:
        """Send a message to this object."""
        self._message_log.append((message, args, kwargs))
        
        if message in self._methods:
            return self._methods[message](self, *args, **kwargs)
        
        if message.startswith("get_"):
            attr = message[4:]
            return self._state.get(attr)
        
        if message.startswith("set_"):
            attr = message[4:]
            self._state[attr] = args[0] if args else kwargs.get('value')
            return self
        
        return self._handle_unknown(message, *args, **kwargs)
    
    def _handle_unknown(self, message: str, *args, **kwargs):
        """Default handler for unknown messages."""
        return None
    
    def introspect(self) -> Dict[str, Any]:
        """Examine object's runtime state."""
        return {
            "name": self.name,
            "methods": list(self._methods.keys()),
            "state": self._state.copy(),
            "recent_messages": self._message_log[-10:]
        }
    
    def clone_with_modifications(self, **modifications) -> 'MessagePassingObject':
        """Create modified clone without stopping runtime."""
        clone = MessagePassingObject(f"{self.name}_clone")
        clone._methods = self._methods.copy()
        clone._state = {**self._state, **modifications}
        return clone

class AltheaRuntime:
    """Runtime environment for message-passing objects."""
    
    def __init__(self):
        self.objects: Dict[str, MessagePassingObject] = {}
    
    def register(self, obj: MessagePassingObject):
        self.objects[obj.name] = obj
    
    def route_message(self, target: str, message: str, *args, **kwargs):
        """Route message to named object."""
        if target in self.objects:
            return self.objects[target].send(message, *args, **kwargs)
        return None

runtime = AltheaRuntime()