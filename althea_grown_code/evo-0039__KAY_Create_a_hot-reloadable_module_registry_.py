import importlib
import sys
from pathlib import Path
from typing import Dict, Callable, Any, Optional
from datetime import datetime
import inspect

class LiveModuleRegistry:
    """Runtime-modifiable module system with message-passing interface."""
    
    def __init__(self, modules_path: str = "./althea_modules"):
        self.modules_path = Path(modules_path)
        self.modules_path.mkdir(exist_ok=True)
        self.active_modules: Dict[str, Any] = {}
        self.module_versions: Dict[str, int] = {}
        self.message_handlers: Dict[str, Callable] = {}
        
    def send(self, module_name: str, message: str, **kwargs) -> Any:
        """Message-passing interface to modules."""
        if module_name not in self.active_modules:
            return {"error": f"Module {module_name} not loaded"}
        
        module = self.active_modules[module_name]
        if hasattr(module, 'handle_message'):
            return module.handle_message(message, **kwargs)
        elif hasattr(module, message):
            handler = getattr(module, message)
            return handler(**kwargs) if callable(handler) else handler
        return {"error": f"Message {message} not understood by {module_name}"}
    
    def hot_reload(self, module_name: str) -> Dict[str, Any]:
        """Reload a module without restarting the system."""
        module_file = self.modules_path / f"{module_name}.py"
        
        if not module_file.exists():
            return {"status": "error", "message": f"Module file {module_file} not found"}
        
        spec = importlib.util.spec_from_file_location(module_name, module_file)
        if spec and spec.loader:
            module = importlib.util.module_from_spec(spec)
            sys.modules[module_name] = module
            spec.loader.exec_module(module)
            
            old_version = self.module_versions.get(module_name, 0)
            new_version = old_version + 1
            
            self.active_modules[module_name] = module
            self.module_versions[module_name] = new_version
            
            return {
                "status": "reloaded",
                "module": module_name,
                "version": f"{old_version} → {new_version}",
                "timestamp": datetime.now().isoformat(),
                "exports": [name for name in dir(module) if not name.startswith('_')]
            }
        
        return {"status": "error", "message": "Failed to load module spec"}
    
    def inject(self, module_name: str, code: str) -> Dict[str, Any]:
        """Inject new code as a module at runtime."""
        module_file = self.modules_path / f"{module_name}.py"
        module_file.write_text(code)
        return self.hot_reload(module_name)
    
    def introspect(self) -> Dict[str, Any]:
        """Return current system state."""
        return {
            "active_modules": list(self.active_modules.keys()),
            "versions": self.module_versions,
            "total_messages_supported": sum(
                len([m for m in dir(mod) if not m.startswith('_')])
                for mod in self.active_modules.values()
            )
        }

registry = LiveModuleRegistry()