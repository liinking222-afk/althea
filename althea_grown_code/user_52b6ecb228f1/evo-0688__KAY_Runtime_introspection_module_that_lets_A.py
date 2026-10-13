import json
import time
from typing import Dict, Any, Optional, Callable

class ModuleRegistry:
    """Late-bound, message-passing registry for live Althea modules."""
    
    def __init__(self):
        self.modules: Dict[str, Dict[str, Any]] = {}
        self.handlers: Dict[str, Callable] = {
            'register': self._handle_register,
            'unregister': self._handle_unregister,
            'query': self._handle_query,
            'mutate': self._handle_mutate,
            'list': self._handle_list,
            'introspect': self._handle_introspect
        }
    
    def send(self, message: str, **kwargs) -> Any:
        """Message-passing interface - all interaction goes through here."""
        handler = self.handlers.get(message)
        if not handler:
            return {'error': f'Unknown message: {message}'}
        return handler(**kwargs)
    
    def _handle_register(self, name: str, version: str, code: str, 
                        metadata: Optional[Dict] = None) -> Dict:
        self.modules[name] = {
            'version': version,
            'code': code,
            'metadata': metadata or {},
            'registered_at': time.time(),
            'mutated_count': 0
        }
        return {'status': 'registered', 'name': name}
    
    def _handle_unregister(self, name: str) -> Dict:
        if name in self.modules:
            del self.modules[name]
            return {'status': 'unregistered', 'name': name}
        return {'error': 'module not found'}
    
    def _handle_query(self, name: str) -> Dict:
        return self.modules.get(name, {'error': 'not found'})
    
    def _handle_mutate(self, name: str, field: str, value: Any) -> Dict:
        if name not in self.modules:
            return {'error': 'module not found'}
        self.modules[name][field] = value
        self.modules[name]['mutated_count'] += 1
        self.modules[name]['last_mutated'] = time.time()
        return {'status': 'mutated', 'name': name, 'field': field}
    
    def _handle_list(self) -> Dict:
        return {name: {'version': m['version'], 'mutated': m['mutated_count']} 
                for name, m in self.modules.items()}
    
    def _handle_introspect(self) -> Dict:
        return {
            'total_modules': len(self.modules),
            'available_messages': list(self.handlers.keys()),
            'module_names': list(self.modules.keys())
        }

# Global runtime-mutable registry
ALTHEA_RUNTIME = ModuleRegistry()