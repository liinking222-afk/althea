import importlib
import sys
import types
import hashlib
from pathlib import Path
from typing import Dict, Any, Callable

class LiveModuleReloader:
    def __init__(self):
        self.module_hashes: Dict[str, str] = {}
        self.message_handlers: Dict[str, Callable] = {}
        
    def _compute_hash(self, filepath: Path) -> str:
        return hashlib.sha256(filepath.read_bytes()).hexdigest()
    
    def register_handler(self, message_type: str, handler: Callable):
        """Register message handler for module communication"""
        self.message_handlers[message_type] = handler
        
    def send_message(self, target_module: str, message_type: str, payload: Any) -> Any:
        """Send message to module handler"""
        handler_key = f"{target_module}.{message_type}"
        if handler_key in self.message_handlers:
            return self.message_handlers[handler_key](payload)
        return None
    
    def hot_reload(self, module_path: str) -> bool:
        """Reload module at runtime if changed"""
        filepath = Path(module_path)
        if not filepath.exists():
            return False
            
        current_hash = self._compute_hash(filepath)
        module_name = filepath.stem
        
        if module_name in self.module_hashes:
            if self.module_hashes[module_name] == current_hash:
                return False
        
        # Reload or load module
        if module_name in sys.modules:
            old_module = sys.modules[module_name]
            new_module = importlib.reload(old_module)
            
            # Re-register message handlers from new module
            if hasattr(new_module, 'register_handlers'):
                new_module.register_handlers(self)
        else:
            spec = importlib.util.spec_from_file_location(module_name, filepath)
            new_module = importlib.util.module_from_spec(spec)
            sys.modules[module_name] = new_module
            spec.loader.exec_module(new_module)
            
            if hasattr(new_module, 'register_handlers'):
                new_module.register_handlers(self)
        
        self.module_hashes[module_name] = current_hash
        return True
    
    def reload_all(self, module_dir: str = "."):
        """Scan and reload all changed modules"""
        reloaded = []
        for pyfile in Path(module_dir).glob("*.py"):
            if self.hot_reload(str(pyfile)):
                reloaded.append(pyfile.stem)
        return reloaded

reloader = LiveModuleReloader()