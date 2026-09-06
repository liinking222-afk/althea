import importlib
import sys
from pathlib import Path
from typing import Dict, Any, Callable, Optional
import hashlib
import time

class LiveModuleRegistry:
    """Kay-style late-binding module system: inspect and reload capabilities at runtime"""
    
    def __init__(self):
        self.modules: Dict[str, Dict[str, Any]] = {}
        self.checksums: Dict[str, str] = {}
        self.message_handlers: Dict[str, Callable] = {}
    
    def register_module(self, name: str, module_path: str, handler: Optional[Callable] = None):
        """Register a module for runtime management"""
        self.modules[name] = {
            'path': module_path,
            'loaded_at': time.time(),
            'reload_count': 0,
            'active': True
        }
        if handler:
            self.message_handlers[name] = handler
        self._update_checksum(name, module_path)
    
    def _update_checksum(self, name: str, path: str):
        """Track module state for change detection"""
        try:
            with open(path, 'rb') as f:
                self.checksums[name] = hashlib.md5(f.read()).hexdigest()
        except FileNotFoundError:
            self.checksums[name] = None
    
    def check_modified(self, name: str) -> bool:
        """Detect if module source has changed"""
        if name not in self.modules:
            return False
        path = self.modules[name]['path']
        old_checksum = self.checksums[name]
        self._update_checksum(name, path)
        return old_checksum != self.checksums[name]
    
    def hot_reload(self, name: str) -> bool:
        """Reload module without stopping system"""
        if name not in self.modules:
            return False
        
        path = self.modules[name]['path']
        module_name = Path(path).stem
        
        if module_name in sys.modules:
            importlib.reload(sys.modules[module_name])
        else:
            importlib.import_module(module_name)
        
        self.modules[name]['reload_count'] += 1
        self.modules[name]['loaded_at'] = time.time()
        return True
    
    def send_message(self, module: str, message: str, payload: Any = None) -> Any:
        """Message-passing interface to modules"""
        if module in self.message_handlers:
            return self.message_handlers[module](message, payload)
        return None
    
    def introspect(self) -> Dict[str, Any]:
        """Runtime self-examination of loaded capabilities"""
        return {
            'module_count': len(self.modules),
            'modules': {k: {**v, 'modified': self.check_modified(k)} 
                       for k, v in self.modules.items()},
            'handlers': list(self.message_handlers.keys())
        }

registry = LiveModuleRegistry()