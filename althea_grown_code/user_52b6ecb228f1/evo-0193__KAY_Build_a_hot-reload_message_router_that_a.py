#!/usr/bin/env python3
import importlib
import inspect
import sys
from pathlib import Path
from typing import Any, Callable, Dict, Optional

class MessageRouter:
    """Late-binding message router for runtime module reloading."""
    
    def __init__(self, module_dir: str = "./modules"):
        self.module_dir = Path(module_dir)
        self.bindings: Dict[str, tuple[str, str]] = {}  # message -> (module_path, function_name)
        self.module_cache: Dict[str, Any] = {}
        self.module_mtimes: Dict[str, float] = {}
        
    def bind(self, message: str, module_path: str, function_name: str) -> None:
        """Bind a message to a module function."""
        self.bindings[message] = (module_path, function_name)
        
    def _load_module(self, module_path: str, force_reload: bool = False) -> Any:
        """Load or reload a module if modified."""
        full_path = self.module_dir / module_path
        
        if not full_path.exists():
            raise FileNotFoundError(f"Module not found: {full_path}")
            
        mtime = full_path.stat().st_mtime
        
        if force_reload or module_path not in self.module_cache or \
           mtime > self.module_mtimes.get(module_path, 0):
            
            spec = importlib.util.spec_from_file_location(
                f"dynamic_{module_path.replace('/', '_')}", full_path
            )
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            
            self.module_cache[module_path] = module
            self.module_mtimes[module_path] = mtime
            
        return self.module_cache[module_path]
    
    def send(self, message: str, *args, **kwargs) -> Any:
        """Send a message, late-binding to current module implementation."""
        if message not in self.bindings:
            raise KeyError(f"No binding for message: {message}")
            
        module_path, function_name = self.bindings[message]
        module = self._load_module(module_path)
        
        if not hasattr(module, function_name):
            raise AttributeError(f"{module_path} has no function {function_name}")
            
        func = getattr(module, function_name)
        return func(*args, **kwargs)
    
    def rebind(self, message: str, module_path: str, function_name: str) -> None:
        """Hot-rebind a message to a different implementation."""
        self.bindings[message] = (module_path, function_name)
        self._load_module(module_path, force_reload=True)
    
    def introspect(self, message: str) -> Optional[str]:
        """Return signature of currently bound function."""
        if message not in self.bindings:
            return None
        module_path, function_name = self.bindings[message]
        module = self._load_module(module_path)
        func = getattr(module, function_name)
        return str(inspect.signature(func))

if __name__ == "__main__":
    router = MessageRouter()
    print("MessageRouter initialized: late-binding enabled")