import importlib
import sys
import inspect
from typing import Any, Callable, Dict, Optional
from pathlib import Path
import hashlib
import json

class LiveModuleSwapper:
    """Kay-inspired runtime module replacement without restart."""
    
    def __init__(self):
        self.module_registry: Dict[str, Dict[str, Any]] = {}
        self.message_bindings: Dict[str, Callable] = {}
        self.evolution_log = []
    
    def register_module(self, name: str, module_path: str, interface: Dict[str, str]):
        """Late-bind a module with its message interface."""
        spec = importlib.util.spec_from_file_location(name, module_path)
        module = importlib.util.module_from_spec(spec)
        
        self.module_registry[name] = {
            'module': module,
            'path': module_path,
            'interface': interface,
            'version': self._hash_file(module_path),
            'loaded': False
        }
    
    def load_module(self, name: str):
        """Lazy load on first message."""
        if name not in self.module_registry:
            raise KeyError(f"Module {name} not registered")
        
        entry = self.module_registry[name]
        if not entry['loaded']:
            spec = importlib.util.spec_from_file_location(name, entry['path'])
            entry['module'] = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(entry['module'])
            entry['loaded'] = True
            
            for msg, func_name in entry['interface'].items():
                self.message_bindings[f"{name}.{msg}"] = getattr(entry['module'], func_name)
    
    def send_message(self, target: str, *args, **kwargs) -> Any:
        """Message-passing dispatch with late binding."""
        if target not in self.message_bindings:
            module_name = target.split('.')[0]
            self.load_module(module_name)
        
        return self.message_bindings[target](*args, **kwargs)
    
    def hot_swap(self, name: str, new_path: str) -> bool:
        """Replace module implementation at runtime."""
        if name not in self.module_registry:
            return False
        
        old_version = self.module_registry[name]['version']
        new_version = self._hash_file(new_path)
        
        spec = importlib.util.spec_from_file_location(name, new_path)
        new_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(new_module)
        
        self.module_registry[name]['module'] = new_module
        self.module_registry[name]['path'] = new_path
        self.module_registry[name]['version'] = new_version
        
        for msg, func_name in self.module_registry[name]['interface'].items():
            self.message_bindings[f"{name}.{msg}"] = getattr(new_module, func_name)
        
        self.evolution_log.append({
            'module': name,
            'old_version': old_version,
            'new_version': new_version,
            'timestamp': importlib.import_module('time').time()
        })
        
        return True
    
    def _hash_file(self, path: str) -> str:
        return hashlib.sha256(Path(path).read_bytes()).hexdigest()[:12]