import inspect
import threading
from typing import Any, Callable, Dict, Optional
from datetime import datetime
from collections import defaultdict

class ModuleRegistry:
    """Runtime-mutable module system with late-bound message passing."""
    
    def __init__(self):
        self._modules: Dict[str, Any] = {}
        self._capabilities: Dict[str, Callable] = {}
        self._message_queue = defaultdict(list)
        self._lock = threading.RLock()
        self._version_history = defaultdict(list)
        
    def register(self, name: str, module: Any, capabilities: Optional[Dict[str, str]] = None):
        """Register or hot-swap a module with optional capability bindings."""
        with self._lock:
            old_version = self._modules.get(name)
            self._modules[name] = module
            self._version_history[name].append({
                'timestamp': datetime.utcnow().isoformat(),
                'version': getattr(module, '__version__', 'unknown')
            })
            
            if capabilities:
                for cap_name, method_name in capabilities.items():
                    if hasattr(module, method_name):
                        self._capabilities[cap_name] = getattr(module, method_name)
            
            self._process_queued_messages(name)
            return old_version
    
    def send_message(self, capability: str, *args, **kwargs):
        """Late-bound message dispatch to registered capabilities."""
        with self._lock:
            if capability in self._capabilities:
                return self._capabilities[capability](*args, **kwargs)
            else:
                self._message_queue[capability].append((args, kwargs))
                return None
    
    def _process_queued_messages(self, module_name: str):
        """Process messages queued for newly registered capabilities."""
        for cap_name in list(self._message_queue.keys()):
            if cap_name in self._capabilities:
                for args, kwargs in self._message_queue.pop(cap_name):
                    self._capabilities[cap_name](*args, **kwargs)
    
    def introspect(self, capability: str) -> Optional[Dict[str, Any]]:
        """Runtime introspection of capability metadata."""
        if capability in self._capabilities:
            func = self._capabilities[capability]
            return {
                'signature': str(inspect.signature(func)),
                'doc': inspect.getdoc(func),
                'source_module': func.__module__
            }
        return None
    
    def get_module_lineage(self, name: str) -> list:
        """Retrieve evolution history of a module."""
        return self._version_history.get(name, [])

registry = ModuleRegistry()