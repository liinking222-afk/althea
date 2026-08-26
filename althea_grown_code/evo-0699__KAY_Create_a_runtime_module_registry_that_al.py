import importlib
import sys
from typing import Dict, Callable, Any, Optional
from datetime import datetime
from pathlib import Path

class ModuleRegistry:
    """Runtime module registry with hot-swapping and message-passing interface."""
    
    def __init__(self):
        self.modules: Dict[str, Any] = {}
        self.bindings: Dict[str, str] = {}  # alias -> module_name
        self.message_handlers: Dict[str, Callable] = {}
        self.load_history: list = []
    
    def register(self, name: str, module_obj: Any, aliases: list = None):
        """Register a module with optional semantic aliases."""
        self.modules[name] = module_obj
        self.bindings[name] = name
        
        for alias in (aliases or []):
            self.bindings[alias] = name
        
        self.load_history.append({
            'timestamp': datetime.utcnow().isoformat(),
            'action': 'register',
            'module': name,
            'aliases': aliases or []
        })
    
    def rebind(self, alias: str, new_target: str):
        """Late-bind: change what a name points to at runtime."""
        if new_target not in self.modules:
            raise KeyError(f"Target module '{new_target}' not registered")
        self.bindings[alias] = new_target
        self.load_history.append({
            'timestamp': datetime.utcnow().isoformat(),
            'action': 'rebind',
            'alias': alias,
            'target': new_target
        })
    
    def send(self, target: str, message: str, **kwargs) -> Any:
        """Message-passing: send message to module by name or alias."""
        module_name = self.bindings.get(target, target)
        module = self.modules.get(module_name)
        
        if module is None:
            raise KeyError(f"Module '{target}' not found")
        
        handler_name = f"handle_{message}"
        if hasattr(module, handler_name):
            return getattr(module, handler_name)(**kwargs)
        elif hasattr(module, message):
            attr = getattr(module, message)
            return attr(**kwargs) if callable(attr) else attr
        else:
            raise AttributeError(f"Module '{module_name}' has no handler for '{message}'")
    
    def hot_reload(self, module_path: str, name: Optional[str] = None):
        """Reload module from filesystem without restart."""
        name = name or Path(module_path).stem
        
        if name in sys.modules:
            importlib.reload(sys.modules[name])
            self.modules[name] = sys.modules[name]
        else:
            spec = importlib.util.spec_from_file_location(name, module_path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            self.modules[name] = module
        
        self.load_history.append({
            'timestamp': datetime.utcnow().isoformat(),
            'action': 'hot_reload',
            'module': name,
            'path': module_path
        })

# Global registry instance
REGISTRY = ModuleRegistry()