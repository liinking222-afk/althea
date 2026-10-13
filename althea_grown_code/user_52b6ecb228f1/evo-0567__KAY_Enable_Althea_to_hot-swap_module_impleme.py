import importlib
import sys
from pathlib import Path
from typing import Any, Callable, Dict, Protocol
import inspect
import json

class MessageHandler(Protocol):
    def handle(self, message: Dict[str, Any]) -> Any: ...

class RuntimeBinder:
    def __init__(self, module_dir: str = "./modules"):
        self.module_dir = Path(module_dir)
        self.module_dir.mkdir(exist_ok=True)
        self.handlers: Dict[str, Callable] = {}
        self.module_versions: Dict[str, int] = {}
        
    def discover_handlers(self):
        """Scan module directory and bind message handlers dynamically."""
        for module_path in self.module_dir.glob("*.py"):
            module_name = module_path.stem
            self._load_module(module_name)
    
    def _load_module(self, module_name: str):
        """Late-bind a module and extract its message handlers."""
        spec = importlib.util.spec_from_file_location(
            module_name, 
            self.module_dir / f"{module_name}.py"
        )
        if not spec or not spec.loader:
            return
        
        module = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = module
        spec.loader.exec_module(module)
        
        for name, obj in inspect.getmembers(module):
            if hasattr(obj, '_message_type'):
                msg_type = obj._message_type
                self.handlers[msg_type] = obj
                self.module_versions[msg_type] = getattr(module, '__version__', 1)
    
    def reload_handler(self, message_type: str):
        """Hot-reload a specific handler without system restart."""
        if message_type in self.handlers:
            handler_module = inspect.getmodule(self.handlers[message_type])
            if handler_module:
                importlib.reload(handler_module)
                self._load_module(handler_module.__name__)
    
    def send(self, message_type: str, payload: Dict[str, Any]) -> Any:
        """Send message to appropriate handler via late binding."""
        if message_type not in self.handlers:
            self.discover_handlers()
        
        handler = self.handlers.get(message_type)
        if handler:
            return handler(payload)
        return {"error": f"No handler for {message_type}"}
    
    def introspect(self) -> Dict[str, Any]:
        """Reveal runtime system state."""
        return {
            "handlers": list(self.handlers.keys()),
            "versions": self.module_versions,
            "module_count": len(self.handlers)
        }

def message_handler(message_type: str):
    """Decorator to mark functions as message handlers."""
    def decorator(func: Callable) -> Callable:
        func._message_type = message_type
        return func
    return decorator