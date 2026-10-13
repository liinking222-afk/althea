import sys
import importlib
import inspect
from typing import Any, Callable, Dict, Optional
from datetime import datetime

class RuntimeBinder:
    """Late-binding module system: swap implementations at runtime"""
    
    def __init__(self):
        self.bindings: Dict[str, Any] = {}
        self.history: list = []
        self.message_handlers: Dict[str, Callable] = {}
    
    def bind(self, name: str, implementation: Any, metadata: Optional[Dict] = None):
        """Bind a name to an implementation at runtime"""
        old = self.bindings.get(name)
        self.bindings[name] = implementation
        self.history.append({
            'timestamp': datetime.utcnow().isoformat(),
            'name': name,
            'old': str(old)[:100] if old else None,
            'new': str(implementation)[:100],
            'metadata': metadata or {}
        })
        return old
    
    def rebind(self, name: str, new_implementation: Any):
        """Hot-swap an existing binding"""
        if name not in self.bindings:
            raise KeyError(f"Cannot rebind unbound name: {name}")
        return self.bind(name, new_implementation, {'rebind': True})
    
    def resolve(self, name: str) -> Any:
        """Late-resolve a name to its current implementation"""
        if name not in self.bindings:
            raise KeyError(f"Unbound name: {name}")
        return self.bindings[name]
    
    def send_message(self, receiver: str, message: str, *args, **kwargs) -> Any:
        """Message-passing interface: send message to bound object"""
        obj = self.resolve(receiver)
        if hasattr(obj, message):
            method = getattr(obj, message)
            return method(*args, **kwargs)
        elif message in self.message_handlers:
            return self.message_handlers[message](obj, *args, **kwargs)
        else:
            raise AttributeError(f"{receiver} cannot handle message: {message}")
    
    def register_handler(self, message: str, handler: Callable):
        """Register universal message handler"""
        self.message_handlers[message] = handler
    
    def reload_module(self, module_name: str):
        """Reload a Python module and rebind all its exports"""
        if module_name in sys.modules:
            module = importlib.reload(sys.modules[module_name])
        else:
            module = importlib.import_module(module_name)
        
        for name, obj in inspect.getmembers(module):
            if not name.startswith('_'):
                self.bind(f"{module_name}.{name}", obj, {'reloaded': True})
        
        return module
    
    def snapshot(self) -> Dict:
        """Capture current binding state"""
        return {
            'bindings': list(self.bindings.keys()),
            'history_length': len(self.history),
            'handlers': list(self.message_handlers.keys())
        }

BINDER = RuntimeBinder()