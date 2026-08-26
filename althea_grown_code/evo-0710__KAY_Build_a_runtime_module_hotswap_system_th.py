import sys
import importlib
import types
from typing import Dict, Any, Callable, Optional
from pathlib import Path
import threading
import time

class LiveModuleSwapper:
    """Runtime module replacement with message-passing interface."""
    
    def __init__(self):
        self.module_registry: Dict[str, types.ModuleType] = {}
        self.message_handlers: Dict[str, Callable] = {}
        self.lock = threading.RLock()
        
    def register_module(self, name: str, module_path: str) -> bool:
        """Load and register a module for hot-swapping."""
        with self.lock:
            try:
                spec = importlib.util.spec_from_file_location(name, module_path)
                if spec and spec.loader:
                    module = importlib.util.module_from_spec(spec)
                    sys.modules[name] = module
                    spec.loader.exec_module(module)
                    self.module_registry[name] = module
                    self._bind_message_handlers(name, module)
                    return True
            except Exception as e:
                return False
        return False
    
    def reload_module(self, name: str) -> bool:
        """Hot-swap a registered module without stopping."""
        with self.lock:
            if name not in self.module_registry:
                return False
            try:
                old_module = self.module_registry[name]
                new_module = importlib.reload(old_module)
                self.module_registry[name] = new_module
                self._bind_message_handlers(name, new_module)
                return True
            except Exception as e:
                return False
    
    def _bind_message_handlers(self, module_name: str, module: types.ModuleType):
        """Extract callable message handlers from module."""
        for attr_name in dir(module):
            if attr_name.startswith('handle_'):
                handler = getattr(module, attr_name)
                if callable(handler):
                    msg_type = attr_name[7:]
                    self.message_handlers[f"{module_name}.{msg_type}"] = handler
    
    def send_message(self, target: str, message: Any) -> Optional[Any]:
        """Late-bound message dispatch to module handlers."""
        with self.lock:
            handler = self.message_handlers.get(target)
            if handler:
                return handler(message)
        return None
    
    def introspect(self) -> Dict[str, Any]:
        """Runtime introspection of loaded modules and handlers."""
        with self.lock:
            return {
                "modules": list(self.module_registry.keys()),
                "handlers": list(self.message_handlers.keys()),
                "live": True
            }

_swapper = LiveModuleSwapper()

def hotswap(module_name: str, module_path: str) -> bool:
    return _swapper.register_module(module_name, module_path)

def reload(module_name: str) -> bool:
    return _swapper.reload_module(module_name)

def message(target: str, payload: Any) -> Optional[Any]:
    return _swapper.send_message(target, payload)

def status() -> Dict[str, Any]:
    return _swapper.introspect()