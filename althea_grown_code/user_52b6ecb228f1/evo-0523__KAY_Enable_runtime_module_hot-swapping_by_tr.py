#!/usr/bin/env python3
import importlib.util
import sys
from pathlib import Path
from typing import Dict, Any, Callable, Optional
from datetime import datetime
import hashlib

class MessagePassingModule:
    """Late-bound module wrapper that handles messages and can be replaced at runtime."""
    
    def __init__(self, name: str, handler: Callable):
        self.name = name
        self.handler = handler
        self.version = datetime.utcnow().isoformat()
        self.message_count = 0
        
    def send(self, message: str, **kwargs) -> Any:
        """Send a message to this module's handler."""
        self.message_count += 1
        return self.handler(message, **kwargs)
    
    def get_signature(self) -> str:
        """Return identity signature for hot-swap verification."""
        return f"{self.name}::{self.version}::{self.message_count}"


class HotSwapRegistry:
    """Runtime registry for late-bound, replaceable modules."""
    
    def __init__(self):
        self.modules: Dict[str, MessagePassingModule] = {}
        self.swap_log = []
        
    def register(self, name: str, handler: Callable) -> None:
        """Register or replace a module at runtime."""
        old_sig = self.modules[name].get_signature() if name in self.modules else None
        self.modules[name] = MessagePassingModule(name, handler)
        self.swap_log.append({
            'name': name,
            'timestamp': datetime.utcnow().isoformat(),
            'old': old_sig,
            'new': self.modules[name].get_signature()
        })
        
    def send_message(self, module_name: str, message: str, **kwargs) -> Any:
        """Late-bound message dispatch to current module version."""
        if module_name not in self.modules:
            raise KeyError(f"Module {module_name} not found in registry")
        return self.modules[module_name].send(message, **kwargs)
    
    def swap_from_file(self, module_name: str, filepath: Path) -> None:
        """Hot-swap module by loading new handler from file."""
        spec = importlib.util.spec_from_file_location(f"runtime_{module_name}", filepath)
        if spec and spec.loader:
            module = importlib.util.module_from_spec(spec)
            sys.modules[spec.name] = module
            spec.loader.exec_module(module)
            if hasattr(module, 'handle'):
                self.register(module_name, module.handle)
                
    def introspect(self) -> Dict[str, Any]:
        """Return current system state for runtime reflection."""
        return {
            'active_modules': list(self.modules.keys()),
            'swap_count': len(self.swap_log),
            'recent_swaps': self.swap_log[-5:],
            'module_signatures': {name: mod.get_signature() 
    for name, mod in self.modules.items()}
        }


# Global runtime registry
_RUNTIME = HotSwapRegistry()

def register_module(name: str, handler: Callable) -> None:
    _RUNTIME.register(name, handler)

def send(module: str, message: str, **kwargs) -> Any:
    return _RUNTIME.send_message(module, message, **kwargs)