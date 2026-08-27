import threading
import time
from typing import Dict, Callable, Any, Optional, List
from dataclasses import dataclass, field

@dataclass
class ModuleVersion:
    implementation: Callable
    version: str
    loaded_at: float
    call_count: int = 0

class RuntimeModuleRegistry:
    def __init__(self):
        self._registry: Dict[str, List[ModuleVersion]] = {}
        self._active: Dict[str, str] = {}
        self._lock = threading.RLock()
    
    def register(self, name: str, implementation: Callable, version: str = "1.0.0") -> None:
        with self._lock:
            if name not in self._registry:
                self._registry[name] = []
                self._active[name] = version
            
            self._registry[name].append(ModuleVersion(
                implementation=implementation,
                version=version,
                loaded_at=time.time()
            ))
    
    def swap(self, name: str, target_version: str) -> bool:
        with self._lock:
            if name not in self._registry:
                return False
            
            versions = [mv.version for mv in self._registry[name]]
            if target_version not in versions:
                return False
            
            self._active[name] = target_version
            return True
    
    def send_message(self, name: str, *args, **kwargs) -> Any:
        with self._lock:
            if name not in self._registry:
                raise ValueError(f"Module '{name}' not registered")
            
            active_version = self._active[name]
            module = next(mv for mv in self._registry[name] if mv.version == active_version)
            module.call_count += 1
            
            return module.implementation(*args, **kwargs)
    
    def introspect(self, name: str) -> Optional[Dict[str, Any]]:
        with self._lock:
            if name not in self._registry:
                return None
            
            return {
                "versions": [mv.version for mv in self._registry[name]],
                "active": self._active[name],
                "statistics": [
                    {"version": mv.version, "calls": mv.call_count, "loaded": mv.loaded_at}
                    for mv in self._registry[name]
                ]
            }

_REGISTRY = RuntimeModuleRegistry()

def register_module(name: str, version: str = "1.0.0"):
    def decorator(func: Callable) -> Callable:
        _REGISTRY.register(name, func, version)
        return func
    return decorator

def message(name: str, *args, **kwargs) -> Any:
    return _REGISTRY.send_message(name, *args, **kwargs)