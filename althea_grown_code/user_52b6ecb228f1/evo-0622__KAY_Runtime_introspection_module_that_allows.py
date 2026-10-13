import importlib
import sys
import time
from typing import Dict, Any, Callable, Optional
from dataclasses import dataclass, field
from collections import defaultdict

@dataclass
class ModuleMessage:
    method: str
    args: tuple = field(default_factory=tuple)
    kwargs: dict = field(default_factory=dict)

@dataclass
class ModuleObject:
    name: str
    module_ref: Any
    loaded_at: float
    call_count: int = 0
    last_called: Optional[float] = None
    
    def send(self, message: ModuleMessage) -> Any:
        """Late-bound message passing to module methods"""
        self.call_count += 1
        self.last_called = time.time()
        method = getattr(self.module_ref, message.method, None)
        if callable(method):
            return method(*message.args, **message.kwargs)
        return None

class RuntimeRegistry:
    def __init__(self):
        self.objects: Dict[str, ModuleObject] = {}
        self.bindings: Dict[str, Callable] = {}
    
    def register(self, name: str, module_path: str) -> ModuleObject:
        """Load or reload a module at runtime"""
        if module_path in sys.modules:
            module_ref = importlib.reload(sys.modules[module_path])
        else:
            module_ref = importlib.import_module(module_path)
        
        obj = ModuleObject(name=name, module_ref=module_ref, loaded_at=time.time())
        self.objects[name] = obj
        return obj
    
    def send(self, target: str, method: str, *args, **kwargs) -> Any:
        """Send message to registered module"""
        if target in self.objects:
            msg = ModuleMessage(method=method, args=args, kwargs=kwargs)
            return self.objects[target].send(msg)
        return None
    
    def introspect(self) -> Dict[str, Any]:
        """Runtime statistics about all modules"""
        return {
            name: {
                "calls": obj.call_count,
                "uptime": time.time() - obj.loaded_at,
                "last_called": obj.last_called
            }
            for name, obj in self.objects.items()
        }
    
    def rebind(self, name: str, target: str, method: str):
        """Create late-bound function alias"""
        self.bindings[name] = lambda *a, **kw: self.send(target, method, *a, **kw)
    
    def __call__(self, binding: str, *args, **kwargs):
        """Invoke bound function by name"""
        if binding in self.bindings:
            return self.bindings[binding](*args, **kwargs)
        return None

REGISTRY = RuntimeRegistry()