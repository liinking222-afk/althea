import json
import inspect
from typing import Any, Callable, Dict, Optional
from pathlib import Path

class MessageBus:
    """Late-binding message-passing system for runtime module composition."""
    
    def __init__(self, registry_path: str = "/tmp/althea_message_bus.json"):
        self.registry_path = Path(registry_path)
        self.handlers: Dict[str, Callable] = {}
        self._load_registry()
    
    def _load_registry(self):
        """Load persisted handler registry."""
        if self.registry_path.exists():
            with open(self.registry_path, 'r') as f:
                data = json.load(f)
                # Registry stores metadata, handlers loaded on demand
                self.registry_meta = data
        else:
            self.registry_meta = {}
    
    def _save_registry(self):
        """Persist handler registry metadata."""
        with open(self.registry_path, 'w') as f:
            json.dump(self.registry_meta, f, indent=2)
    
    def register(self, message_type: str, handler: Callable, description: str = ""):
        """Register a handler for a message type."""
        self.handlers[message_type] = handler
        self.registry_meta[message_type] = {
            "description": description,
            "signature": str(inspect.signature(handler)),
            "module": handler.__module__
        }
        self._save_registry()
    
    def unregister(self, message_type: str):
        """Remove a handler at runtime."""
        self.handlers.pop(message_type, None)
        self.registry_meta.pop(message_type, None)
        self._save_registry()
    
    def send(self, message_type: str, payload: Any) -> Optional[Any]:
        """Send a message to registered handler."""
        handler = self.handlers.get(message_type)
        if handler:
            return handler(payload)
        return None
    
    def discover(self) -> Dict[str, Dict]:
        """Return all available message types and their metadata."""
        return self.registry_meta
    
    def introspect(self, message_type: str) -> Optional[Dict]:
        """Get metadata about a specific message type."""
        return self.registry_meta.get(message_type)

# Global singleton instance
_bus = MessageBus()

def register_handler(message_type: str, description: str = ""):
    """Decorator for registering message handlers."""
    def decorator(func: Callable):
        _bus.register(message_type, func, description)
        return func
    return decorator

def send_message(message_type: str, payload: Any) -> Optional[Any]:
    return _bus.send(message_type, payload)

def discover_handlers() -> Dict[str, Dict]:
    return _bus.discover()