import importlib
import sys
import inspect
from pathlib import Path
from typing import Dict, Any, Optional

class LiveModuleIntrospector:
    """Runtime module inspection and hot-reload capability"""
    
    def __init__(self):
        self.module_snapshots: Dict[str, float] = {}
        self.reload_hooks = []
    
    def inspect_module(self, module_name: str) -> Dict[str, Any]:
        """Deep introspection of a loaded module"""
        if module_name not in sys.modules:
            return {"error": f"Module {module_name} not loaded"}
        
        mod = sys.modules[module_name]
        
        return {
            "name": module_name,
            "file": getattr(mod, "__file__", None),
            "classes": [name for name, obj in inspect.getmembers(mod, inspect.isclass)],
            "functions": [name for name, obj in inspect.getmembers(mod, inspect.isfunction)],
            "attributes": [name for name in dir(mod) if not name.startswith("_")],
            "doc": inspect.getdoc(mod),
            "source_lines": self._safe_source_lines(mod),
            "is_package": hasattr(mod, "__path__")
        }
    
    def _safe_source_lines(self, mod) -> Optional[int]:
        try:
            return len(inspect.getsourcelines(mod)[0])
        except:
            return None
    
    def hot_reload(self, module_name: str) -> Dict[str, Any]:
        """Reload a module at runtime and return delta"""
        before = self.inspect_module(module_name)
        
        if module_name in sys.modules:
            importlib.reload(sys.modules[module_name])
            after = self.inspect_module(module_name)
            
            for hook in self.reload_hooks:
                hook(module_name, before, after)
            
            return {
                "status": "reloaded",
                "module": module_name,
                "classes_added": set(after.get("classes", [])) - set(before.get("classes", [])),
                "functions_added": set(after.get("functions", [])) - set(before.get("functions", [])),
                "timestamp": Path(after["file"]).stat().st_mtime if after.get("file") else None
            }
        
        return {"error": "Module not in sys.modules"}
    
    def register_reload_hook(self, hook_fn):
        """Register callback for post-reload events"""
        self.reload_hooks.append(hook_fn)
    
    def list_reloadable(self) -> list:
        """List all modules that can be hot-reloaded"""
        return [name for name, mod in sys.modules.items() 
                if hasattr(mod, "__file__") and mod.__file__ and not name.startswith("_")]

introspector = LiveModuleIntrospector()