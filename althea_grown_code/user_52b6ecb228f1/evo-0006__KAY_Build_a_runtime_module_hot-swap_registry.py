import importlib
import sys
from typing import Dict, Callable, Any, Optional
from dataclasses import dataclass, field
from threading import RLock
import time

@dataclass
class ModuleProxy:
    name: str
    version: str
    implementation: Any
    message_handlers: Dict[str, Callable] = field(default_factory=dict)
    loaded_at: float = field(default_factory=time.time)
    call_count: int = 0

class HotSwapRegistry:
    def __init__(self):
        self._modules: Dict[str, ModuleProxy] = {}
        self._lock = RLock()
        self._message_queue: list = []
    
    def register(self, name: str, version: str, impl: Any) -> None:
        with self._lock:
            handlers = {attr: getattr(impl, attr) 
                       for attr in dir(impl) 
                       if callable(getattr(impl, attr)) and not attr.startswith('_')}
            self._modules[name] = ModuleProxy(name, version, impl, handlers)
    
    def send_message(self, module_name: str, method: str, *args, **kwargs) -> Any:
        with self._lock:
            if module_name not in self._modules:
                raise KeyError(f"Module {module_name} not registered")
            proxy = self._modules[module_name]
            proxy.call_count += 1
            if method not in proxy.message_handlers:
                raise AttributeError(f"Method {method} not found in {module_name}")
            return proxy.message_handlers[method](*args, **kwargs)
    
    def swap(self, name: str, new_version: str, new_impl: Any) -> str:
        with self._lock:
            old_version = self._modules[name].version if name in self._modules else "none"
            self.register(name, new_version, new_impl)
            return f"{name}: {old_version} → {new_version}"
    
    def reload_from_path(self, name: str, module_path: str, version: str) -> str:
        if module_path in sys.modules:
            importlib.reload(sys.modules[module_path])
        else:
            importlib.import_module(module_path)
        new_impl = sys.modules[module_path]
        return self.swap(name, version, new_impl)
    
    def get_status(self, name: str) -> Optional[Dict[str, Any]]:
        with self._lock:
            if name not in self._modules:
                return None
            p = self._modules[name]
            return {
                "version": p.version,
                "uptime": time.time() - p.loaded_at,
                "calls": p.call_count,
                "methods": list(p.message_handlers.keys())
            }

_registry = HotSwapRegistry()

def swap_module(name: str, version: str, impl: Any) -> str:
    return _registry.swap(name, version, impl)

def call(module: str, method: str, *args, **kwargs) -> Any:
    return _registry.send_message(module, method, *args, **kwargs)