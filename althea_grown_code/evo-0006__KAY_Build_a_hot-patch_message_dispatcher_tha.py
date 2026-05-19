import inspect
import threading
from typing import Any, Callable, Dict, Optional
from functools import wraps

class MessageDispatcher:
    def __init__(self):
        self._interceptors: Dict[str, Callable] = {}
        self._lock = threading.RLock()
        self._call_log = []
        
    def wrap(self, obj: Any, method_name: str) -> None:
        """Wrap a method to enable runtime interception"""
        original = getattr(obj, method_name)
        
        @wraps(original)
        def proxy(*args, **kwargs):
            key = f"{obj.__class__.__name__}.{method_name}"
            
            with self._lock:
                interceptor = self._interceptors.get(key)
                self._call_log.append({
                    'target': key,
                    'intercepted': interceptor is not None
                })
                
            if interceptor:
                return interceptor(original, *args, **kwargs)
            return original(*args, **kwargs)
        
        setattr(obj, method_name, proxy)
    
    def intercept(self, target: str, handler: Optional[Callable] = None) -> None:
        """Install or remove runtime behavior modifier"""
        with self._lock:
            if handler is None:
                self._interceptors.pop(target, None)
            else:
                self._interceptors[target] = handler
    
    def wrap_module(self, obj: Any) -> None:
        """Wrap all callable methods of an object"""
        for name, method in inspect.getmembers(obj, predicate=inspect.ismethod):
            if not name.startswith('_'):
                self.wrap(obj, name)
    
    def get_log(self) -> list:
        """Retrieve interception activity log"""
        with self._lock:
            return list(self._call_log)
    
    def clear_log(self) -> None:
        with self._lock:
            self._call_log.clear()

# Global dispatcher instance
dispatcher = MessageDispatcher()

def late_bind(obj: Any) -> Any:
    """Make any object runtime-modifiable"""
    dispatcher.wrap_module(obj)
    return obj