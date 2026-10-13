import threading
import importlib.util
import sys
from typing import Dict, Any, Callable, Optional
from pathlib import Path
import time

class ModuleRegistry:
    """Late-binding module registry with message-passing interface."""
    
    def __init__(self):
        self._modules: Dict[str, Any] = {}
        self._handlers: Dict[str, Callable] = {}
        self._lock = threading.RLock()
        self._message_queue = []
        
    def register(self, name: str, module_path: Optional[str] = None, obj: Any = None):
        """Dynamically load and register a module at runtime."""
        with self._lock:
            if module_path:
                spec = importlib.util.spec_from_file_location(name, module_path)
                module = importlib.util.module_from_spec(spec)
                sys.modules[name] = module
                spec.loader.exec_module(module)
                self._modules[name] = module
            elif obj:
                self._modules[name] = obj
            
    def unregister(self, name: str):
        """Remove module from registry."""
        with self._lock:
            if name in self._modules:
                del self._modules[name]
                if name in sys.modules:
                    del sys.modules[name]
                    
    def send(self, target: str, message: str, **kwargs) -> Any:
        """Send message to registered module."""
        with self._lock:
            if target not in self._modules:
                raise ValueError(f"Module {target} not registered")
            module = self._modules[target]
            if hasattr(module, 'handle_message'):
                return module.handle_message(message, **kwargs)
            elif hasattr(module, message):
                return getattr(module, message)(**kwargs)
            else:
                raise AttributeError(f"Module {target} cannot handle '{message}'")
    
    def hot_swap(self, name: str, new_path: str):
        """Replace module without stopping system."""
        with self._lock:
            self.unregister(name)
            self.register(name, new_path)
            
    def introspect(self, name: str) -> Dict[str, Any]:
        """Query module capabilities."""
        with self._lock:
            if name not in self._modules:
                return {}
            module = self._modules[name]
            return {
                'methods': [m for m in dir(module) if not m.startswith('_')],
                'type': type(module).__name__,
                'timestamp': time.time()
            }
    
    def list_modules(self) -> list:
        """Return all registered module names."""
        with self._lock:
            return list(self._modules.keys())

registry = ModuleRegistry()