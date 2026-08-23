import importlib
import sys
from typing import Any, Callable, Dict, Optional
from pathlib import Path
from datetime import datetime

class RuntimeModuleRegistry:
    """Late-binding module registry for live system modification."""
    
    def __init__(self):
        self._modules: Dict[str, Any] = {}
        self._bindings: Dict[str, str] = {}
        self._message_handlers: Dict[str, Callable] = {}
        self._load_history: list = []
    
    def bind(self, interface: str, module_path: str) -> None:
        """Late-bind an interface name to a module implementation."""
        self._bindings[interface] = module_path
        self._load_history.append({
            'interface': interface,
            'module': module_path,
            'timestamp': datetime.utcnow().isoformat()
        })
    
    def send_message(self, interface: str, message: str, *args, **kwargs) -> Any:
        """Message-passing interface to bound modules."""
        if interface not in self._bindings:
            raise ValueError(f"No binding for interface '{interface}'")
        
        module = self._get_or_load(interface)
        handler = self._message_handlers.get(interface)
        
        if handler:
            return handler(message, *args, **kwargs)
        
        if hasattr(module, message):
            return getattr(module, message)(*args, **kwargs)
        
        raise AttributeError(f"Module has no handler for message '{message}'")
    
    def _get_or_load(self, interface: str) -> Any:
        module_path = self._bindings[interface]
        
        if interface in self._modules:
            return self._modules[interface]
        
        spec = importlib.util.spec_from_file_location(interface, module_path)
        module = importlib.util.module_from_spec(spec)
        sys.modules[interface] = module
        spec.loader.exec_module(module)
        
        self._modules[interface] = module
        return module
    
    def reload(self, interface: str) -> None:
        """Hot-reload a module while system is running."""
        if interface in self._modules:
            del self._modules[interface]
        self._get_or_load(interface)
    
    def register_handler(self, interface: str, handler: Callable) -> None:
        """Register custom message handler for an interface."""
        self._message_handlers[interface] = handler
    
    def introspect(self) -> Dict:
        """Return current system state - objects all the way down."""
        return {
            'bindings': self._bindings,
            'loaded': list(self._modules.keys()),
            'handlers': list(self._message_handlers.keys()),
            'history': self._load_history
        }

registry = RuntimeModuleRegistry()