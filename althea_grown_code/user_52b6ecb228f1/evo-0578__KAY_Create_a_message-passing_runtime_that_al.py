import inspect
import threading
from typing import Any, Callable, Dict, Protocol
from dataclasses import dataclass, field
from collections import defaultdict

@dataclass
class Message:
    selector: str
    args: tuple
    kwargs: dict
    reply_to: Any = None

class MessagePassingRuntime:
    def __init__(self):
        self._objects: Dict[str, Any] = {}
        self._implementations: Dict[str, Dict[str, Callable]] = defaultdict(dict)
        self._message_queue: list = []
        self._lock = threading.RLock()
        
    def register_object(self, name: str, obj: Any):
        with self._lock:
            self._objects[name] = obj
            for method_name in dir(obj):
                if not method_name.startswith('_'):
                    method = getattr(obj, method_name)
                    if callable(method):
                        self._implementations[name][method_name] = method
    
    def hot_swap(self, name: str, selector: str, new_impl: Callable):
        with self._lock:
            if name not in self._implementations:
                self._implementations[name] = {}
            old_impl = self._implementations[name].get(selector)
            self._implementations[name][selector] = new_impl
            return old_impl
    
    def send_message(self, target: str, selector: str, *args, **kwargs) -> Any:
        with self._lock:
            if target not in self._implementations:
                raise ValueError(f"Unknown object: {target}")
            if selector not in self._implementations[target]:
                raise ValueError(f"Unknown selector: {selector} on {target}")
            impl = self._implementations[target][selector]
        return impl(*args, **kwargs)
    
    def introspect(self, target: str) -> Dict[str, str]:
        with self._lock:
            if target not in self._implementations:
                return {}
            return {
                sel: inspect.signature(impl).return_annotation.__name__ 
                if hasattr(inspect.signature(impl).return_annotation, '__name__') 
                else 'Any'
                for sel, impl in self._implementations[target].items()
            }

runtime = MessagePassingRuntime()

def evolve_at_runtime(target: str, selector: str):
    def decorator(func: Callable):
        runtime.hot_swap(target, selector, func)
        return func
    return decorator