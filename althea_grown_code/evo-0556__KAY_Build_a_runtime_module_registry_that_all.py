import importlib
import sys
from typing import Dict, Any, Callable, Optional
from datetime import datetime
import inspect

class MessagePassingRegistry:
    """Alan Kay-inspired runtime module system with late binding and message passing."""
    
    def __init__(self):
        self.modules: Dict[str, Dict[str, Any]] = {}
        self.message_handlers: Dict[str, Callable] = {}
        self.version_history: Dict[str, list] = {}
    
    def register_module(self, name: str, handler: Callable, version: str = "1.0.0", metadata: Optional[Dict] = None):
        """Register or hot-swap a module at runtime."""
        if name not in self.version_history:
            self.version_history[name] = []
        
        self.version_history[name].append({
            'version': version,
            'timestamp': datetime.utcnow().isoformat(),
            'metadata': metadata or {}
        })
        
        self.modules[name] = {
            'handler': handler,
            'version': version,
            'metadata': metadata or {},
            'signature': inspect.signature(handler)
        }
        
        self.message_handlers[name] = handler
    
    def send_message(self, module_name: str, *args, **kwargs) -> Any:
        """Late-bound message passing to module."""
        if module_name not in self.message_handlers:
            raise KeyError(f"Module '{module_name}' not found in registry")
        return self.message_handlers[module_name](*args, **kwargs)
    
    def hot_swap(self, name: str, new_handler: Callable, version: str):
        """Replace module implementation without system restart."""
        old_version = self.modules.get(name, {}).get('version', 'none')
        self.register_module(name, new_handler, version, {'replaced': old_version})
        return f"{name}: {old_version} → {version}"
    
    def introspect(self, module_name: str) -> Dict[str, Any]:
        """Runtime introspection of module capabilities."""
        if module_name not in self.modules:
            return {}
        mod = self.modules[module_name]
        return {
            'version': mod['version'],
            'signature': str(mod['signature']),
            'history': self.version_history[module_name],
            'metadata': mod['metadata']
        }
    
    def list_modules(self) -> Dict[str, str]:
        """Enumerate all registered capabilities."""
        return {name: mod['version'] for name, mod in self.modules.items()}

# Global instance for Althea's runtime
RUNTIME = MessagePassingRegistry()