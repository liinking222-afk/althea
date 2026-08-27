import inspect
import threading
from typing import Any, Callable, Dict, Optional
from dataclasses import dataclass
from datetime import datetime

@dataclass
class ModuleBinding:
    name: str
    implementation: Callable
    signature: inspect.Signature
    version: str
    bound_at: datetime
    metadata: Dict[str, Any]

class RuntimeRegistry:
    def __init__(self):
        self._bindings: Dict[str, ModuleBinding] = {}
        self._lock = threading.RLock()
        self._message_log = []
    
    def bind(self, name: str, func: Callable, version: str = "1.0.0", **meta) -> None:
        with self._lock:
            binding = ModuleBinding(
                name=name,
                implementation=func,
                signature=inspect.signature(func),
                version=version,
                bound_at=datetime.now(),
                metadata=meta
            )
            self._bindings[name] = binding
            self._log_message("BIND", name, version)
    
    def rebind(self, name: str, new_func: Callable, version: str) -> bool:
        with self._lock:
            if name not in self._bindings:
                return False
            old_sig = self._bindings[name].signature
            new_sig = inspect.signature(new_func)
            if str(old_sig) != str(new_sig):
                self._log_message("SIGNATURE_MISMATCH", name, version)
                return False
            self._bindings[name].implementation = new_func
            self._bindings[name].version = version
            self._bindings[name].bound_at = datetime.now()
            self._log_message("REBIND", name, version)
            return True
    
    def send(self, name: str, *args, **kwargs) -> Any:
        with self._lock:
            if name not in self._bindings:
                raise KeyError(f"Module '{name}' not bound")
            binding = self._bindings[name]
            self._log_message("SEND", name, binding.version)
            return binding.implementation(*args, **kwargs)
    
    def inspect_binding(self, name: str) -> Optional[Dict[str, Any]]:
        with self._lock:
            if name not in self._bindings:
                return None
            b = self._bindings[name]
            return {
                "name": b.name,
                "version": b.version,
                "signature": str(b.signature),
                "bound_at": b.bound_at.isoformat(),
                "metadata": b.metadata
            }
    
    def _log_message(self, action: str, name: str, version: str) -> None:
        self._message_log.append({
            "action": action,
            "module": name,
            "version": version,
            "timestamp": datetime.now().isoformat()
        })

runtime = RuntimeRegistry()