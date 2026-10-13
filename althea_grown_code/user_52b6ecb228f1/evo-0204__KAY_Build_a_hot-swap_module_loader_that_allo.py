import importlib.util
import sys
from typing import Dict, Callable, Any, Optional
from pathlib import Path
import hashlib
import time

class MessagePassingRuntime:
    """Alan Kay-inspired runtime that treats modules as message-passing objects."""
    
    def __init__(self):
        self.modules: Dict[str, Any] = {}
        self.message_handlers: Dict[str, Callable] = {}
        self.module_hashes: Dict[str, str] = {}
        self.binding_table: Dict[str, str] = {}
    
    def load_module(self, name: str, path: str) -> bool:
        """Late-bind a module into the running system."""
        try:
            spec = importlib.util.spec_from_file_location(name, path)
            if not spec or not spec.loader:
                return False
            
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            
            content_hash = hashlib.sha256(Path(path).read_bytes()).hexdigest()[:8]
            
            self.modules[name] = module
            self.module_hashes[name] = content_hash
            
            if hasattr(module, 'register_handlers'):
                handlers = module.register_handlers()
                for msg_type, handler in handlers.items():
                    self.message_handlers[msg_type] = handler
                    self.binding_table[msg_type] = name
            
            return True
        except Exception:
            return False
    
    def unload_module(self, name: str) -> bool:
        """Remove module and its bindings from runtime."""
        if name not in self.modules:
            return False
        
        handlers_to_remove = [k for k, v in self.binding_table.items() if v == name]
        for handler in handlers_to_remove:
            del self.message_handlers[handler]
            del self.binding_table[handler]
        
        del self.modules[name]
        del self.module_hashes[name]
        
        if name in sys.modules:
            del sys.modules[name]
        
        return True
    
    def hot_swap(self, name: str, path: str) -> bool:
        """Replace running module without system restart."""
        self.unload_module(name)
        return self.load_module(name, path)
    
    def send_message(self, msg_type: str, payload: Any) -> Optional[Any]:
        """Send message to dynamically-bound handler."""
        if msg_type in self.message_handlers:
            return self.message_handlers[msg_type](payload)
        return None
    
    def introspect(self) -> Dict[str, Any]:
        """Runtime reflection of current bindings."""
        return {
            "modules": list(self.modules.keys()),
            "handlers": self.binding_table,
            "hashes": self.module_hashes
        }

_runtime = MessagePassingRuntime()

def load(name: str, path: str) -> bool:
    return _runtime.load_module(name, path)

def swap(name: str, path: str) -> bool:
    return _runtime.hot_swap(name, path)

def send(msg_type: str, payload: Any) -> Optional[Any]:
    return _runtime.send_message(msg_type, payload)