import importlib
import importlib.util
import sys
from pathlib import Path
from typing import Dict, Any, Callable, Optional
import threading
import time
import hashlib

class ModuleRegistry:
    def __init__(self, module_dir: str = "./modules"):
        self.module_dir = Path(module_dir)
        self.module_dir.mkdir(exist_ok=True)
        self.registry: Dict[str, Dict[str, Any]] = {}
        self.lock = threading.RLock()
        self.file_hashes: Dict[str, str] = {}
        
    def _compute_hash(self, filepath: Path) -> str:
        return hashlib.sha256(filepath.read_bytes()).hexdigest()
    
    def send_message(self, module_name: str, message: str, **kwargs) -> Any:
        with self.lock:
            if module_name not in self.registry:
                self._load_module(module_name)
            module_obj = self.registry[module_name]["instance"]
            if hasattr(module_obj, "receive"):
                return module_obj.receive(message, **kwargs)
            raise AttributeError(f"Module {module_name} has no receive method")
    
    def _load_module(self, module_name: str) -> None:
        filepath = self.module_dir / f"{module_name}.py"
        if not filepath.exists():
            raise FileNotFoundError(f"Module {module_name} not found")
        
        spec = importlib.util.spec_from_file_location(module_name, filepath)
        module = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = module
        spec.loader.exec_module(module)
        
        instance = module.Module() if hasattr(module, "Module") else module
        self.registry[module_name] = {
            "module": module,
            "instance": instance,
            "path": filepath,
            "loaded_at": time.time()
        }
        self.file_hashes[module_name] = self._compute_hash(filepath)
    
    def reload_if_changed(self, module_name: str) -> bool:
        with self.lock:
            if module_name not in self.registry:
                return False
            filepath = self.registry[module_name]["path"]
            current_hash = self._compute_hash(filepath)
            if current_hash != self.file_hashes[module_name]:
                self._load_module(module_name)
                return True
            return False
    
    def scan_and_reload(self) -> int:
        reloaded = 0
        with self.lock:
            for module_name in list(self.registry.keys()):
                if self.reload_if_changed(module_name):
                    reloaded += 1
        return reloaded

registry = ModuleRegistry()