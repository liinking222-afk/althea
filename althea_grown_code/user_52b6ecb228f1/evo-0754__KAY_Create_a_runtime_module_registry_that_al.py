#!/usr/bin/env python3
"""Runtime Module Registry - Late-binding capability orchestration"""
import importlib.util
import sys
from pathlib import Path
from typing import Any, Callable, Dict, Optional
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class ModuleEnvelope:
    """Message-passing wrapper for runtime modules"""
    path: Path
    version: str
    loaded_at: datetime
    interface: Dict[str, Callable] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    _module: Any = None
    
    def send(self, message: str, *args, **kwargs) -> Any:
        """Message-passing interface to module capabilities"""
        if message in self.interface:
            return self.interface[message](*args, **kwargs)
        raise AttributeError(f"Module does not respond to '{message}'")


class RuntimeRegistry:
    """Late-binding module registry with hot-swap capability"""
    
    def __init__(self):
        self.modules: Dict[str, ModuleEnvelope] = {}
        self.aliases: Dict[str, str] = {}
    
    def register(self, name: str, module_path: Path, version: str = "1.0.0") -> ModuleEnvelope:
        """Dynamically load and register a module at runtime"""
        spec = importlib.util.spec_from_file_location(name, module_path)
        module = importlib.util.module_from_spec(spec)
        sys.modules[name] = module
        spec.loader.exec_module(module)
        
        interface = {attr: getattr(module, attr) 
                    for attr in dir(module) 
                    if callable(getattr(module, attr)) and not attr.startswith('_')}
        
        envelope = ModuleEnvelope(
            path=module_path,
            version=version,
            loaded_at=datetime.now(),
            interface=interface,
            metadata=getattr(module, '__metadata__', {}),
            _module=module
        )
        
        self.modules[name] = envelope
        return envelope
    
    def swap(self, name: str, new_path: Path, new_version: str) -> ModuleEnvelope:
        """Hot-swap a running module with zero downtime"""
        return self.register(name, new_path, new_version)
    
    def send_to(self, module_name: str, message: str, *args, **kwargs) -> Any:
        """Send message to named module (late-binding dispatch)"""
        target = self.aliases.get(module_name, module_name)
        if target not in self.modules:
            raise KeyError(f"Module '{target}' not found in registry")
        return self.modules[target].send(message, *args, **kwargs)
    
    def alias(self, name: str, target: str):
        """Create semantic alias for indirection layer"""
        self.aliases[name] = target


registry = RuntimeRegistry()