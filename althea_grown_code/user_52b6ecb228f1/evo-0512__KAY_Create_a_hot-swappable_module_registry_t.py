import inspect
import threading
from typing import Any, Callable, Dict, Optional
from datetime import datetime

class LiveModuleRegistry:
    """Kay-inspired runtime module hot-swap system with message-passing interface."""
    
    def __init__(self):
        self._modules: Dict[str, Dict[str, Any]] = {}
        self._lock = threading.RLock()
        self._message_queue = []
        self._version_history: Dict[str, list] = {}
    
    def register(self, name: str, fn: Callable, metadata: Optional[Dict] = None):
        """Register or hot-swap a module at runtime."""
        with self._lock:
            version = len(self._version_history.get(name, [])) + 1
            module_entry = {
                'function': fn,
                'metadata': metadata or {},
                'version': version,
                'registered_at': datetime.utcnow().isoformat(),
                'source': inspect.getsource(fn) if not inspect.isbuiltin(fn) else '<builtin>'
            }
            self._modules[name] = module_entry
            
            if name not in self._version_history:
                self._version_history[name] = []
            self._version_history[name].append(module_entry)
            
            return {'status': 'registered', 'name': name, 'version': version}
    
    def send_message(self, target: str, *args, **kwargs):
        """Message-passing invocation - late-bound at call time."""
        with self._lock:
            if target not in self._modules:
                return {'error': f'Module {target} not found', 'available': list(self._modules.keys())}
            
            module = self._modules[target]
            try:
                result = module['function'](*args, **kwargs)
                return {'result': result, 'version': module['version'], 'target': target}
            except Exception as e:
                return {'error': str(e), 'target': target, 'version': module['version']}
    
    def introspect(self, name: Optional[str] = None):
        """Runtime introspection of live modules."""
        with self._lock:
            if name:
                return self._modules.get(name, {'error': 'not found'})
            return {k: {'version': v['version'], 'registered_at': v['registered_at']} 
                    for k, v in self._modules.items()}
    
    def rollback(self, name: str, version: Optional[int] = None):
        """Rollback to previous version of a module."""
        with self._lock:
            if name not in self._version_history or not self._version_history[name]:
                return {'error': 'No history found'}
            
            target_version = version or len(self._version_history[name]) - 1
            if target_version < 1 or target_version > len(self._version_history[name]):
                return {'error': 'Invalid version'}
            
            self._modules[name] = self._version_history[name][target_version - 1]
            return {'status': 'rolled_back', 'name': name, 'version': target_version}

registry = LiveModuleRegistry()