import threading
import time
from typing import Any, Callable, Dict, Optional
from collections import defaultdict

class MessagePassingRegistry:
    """Late-binding module registry with runtime rebinding capabilities."""
    
    def __init__(self):
        self._modules: Dict[str, Any] = {}
        self._message_handlers: Dict[str, Dict[str, Callable]] = defaultdict(dict)
        self._lock = threading.RLock()
        self._version_map: Dict[str, int] = defaultdict(int)
    
    def register_module(self, name: str, module: Any, handlers: Dict[str, Callable] = None):
        """Register or hot-swap a module at runtime."""
        with self._lock:
            self._modules[name] = module
            self._version_map[name] += 1
            if handlers:
                self._message_handlers[name] = handlers
            return self._version_map[name]
    
    def send_message(self, target: str, message: str, *args, **kwargs) -> Any:
        """Send message to module; late-binds at call time."""
        with self._lock:
            if target not in self._modules:
                raise KeyError(f"Module {target} not registered")
            handlers = self._message_handlers.get(target, {})
            if message not in handlers:
                if hasattr(self._modules[target], message):
                    return getattr(self._modules[target], message)(*args, **kwargs)
                raise AttributeError(f"Module {target} has no handler for '{message}'")
            return handlers[message](*args, **kwargs)
    
    def rebind(self, source: str, dependency: str, new_target: str):
        """Rebind a module's dependency without restart."""
        with self._lock:
            if source in self._message_handlers:
                for msg, handler in self._message_handlers[source].items():
                    if hasattr(handler, '__rebind__'):
                        handler.__rebind__(dependency, new_target)
            self._version_map[f"{source}->{dependency}"] += 1
    
    def get_module(self, name: str) -> Optional[Any]:
        """Retrieve current module instance."""
        with self._lock:
            return self._modules.get(name)
    
    def list_modules(self) -> Dict[str, int]:
        """Return all modules with their version numbers."""
        with self._lock:
            return {name: self._version_map[name] for name in self._modules.keys()}

_GLOBAL_REGISTRY = MessagePassingRegistry()

def get_registry() -> MessagePassingRegistry:
    return _GLOBAL_REGISTRY