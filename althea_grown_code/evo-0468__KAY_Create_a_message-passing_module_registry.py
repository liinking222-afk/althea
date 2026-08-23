import importlib.util
import sys
from pathlib import Path
from typing import Dict, Any, Callable, Optional
from datetime import datetime
import hashlib

class MessagePassingModuleRegistry:
    """Late-binding module system - swap implementations without restart."""
    
    def __init__(self, modules_path: str = "./althea_modules"):
        self.modules_path = Path(modules_path)
        self.modules_path.mkdir(exist_ok=True)
        self._registry: Dict[str, Dict[str, Any]] = {}
        self._message_handlers: Dict[str, Callable] = {}
    
    def register(self, name: str, filepath: Path, entry_point: str = "handle"):
        """Register or hot-swap a module by loading from disk."""
        spec = importlib.util.spec_from_file_location(name, filepath)
        if spec and spec.loader:
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            
            handler = getattr(module, entry_point, None)
            if not callable(handler):
                raise ValueError(f"Entry point '{entry_point}' not callable in {name}")
            
            file_hash = hashlib.sha256(filepath.read_bytes()).hexdigest()[:8]
            
            self._registry[name] = {
                "handler": handler,
                "filepath": filepath,
                "loaded_at": datetime.utcnow().isoformat(),
                "hash": file_hash,
                "version": getattr(module, "__version__", "0.0.0")
            }
            self._message_handlers[name] = handler
            return file_hash
    
    def send(self, module_name: str, message: Any) -> Any:
        """Send message to module - Kay's message-passing paradigm."""
        if module_name not in self._message_handlers:
            raise KeyError(f"Module '{module_name}' not registered")
        return self._message_handlers[module_name](message)
    
    def reload(self, name: str) -> str:
        """Hot-reload module from disk without system restart."""
        if name not in self._registry:
            raise KeyError(f"Module '{name}' not found")
        filepath = self._registry[name]["filepath"]
        return self.register(name, filepath)
    
    def list_modules(self) -> Dict[str, Dict[str, Any]]:
        """Inspect live system state."""
        return {k: {kk: vv for kk, vv in v.items() if kk != "handler"} 
                for k, v in self._registry.items()}
    
    def discover_and_load(self) -> int:
        """Auto-discover .py modules in directory and load them."""
        count = 0
        for py_file in self.modules_path.glob("*.py"):
            if not py_file.name.startswith("_"):
                try:
                    self.register(py_file.stem, py_file)
                    count += 1
                except Exception:
                    pass
        return count

registry = MessagePassingModuleRegistry()