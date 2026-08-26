#!/usr/bin/env python3
import os
import time
import importlib
import sys
from pathlib import Path
from typing import Dict, Any, Callable
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

class ModuleHotReloader(FileSystemEventHandler):
    def __init__(self, module_registry: Dict[str, Any]):
        self.registry = module_registry
        self.module_cache = {}
        self.last_reload = {}
        
    def on_modified(self, event):
        if event.is_directory or not event.src_path.endswith('.py'):
            return
            
        path = Path(event.src_path)
        module_name = path.stem
        
        # Debounce: prevent reload spam
        now = time.time()
        if module_name in self.last_reload:
            if now - self.last_reload[module_name] < 0.5:
                return
        
        self.hot_reload(module_name, str(path.parent))
        self.last_reload[module_name] = now
    
    def hot_reload(self, module_name: str, module_path: str):
        try:
            if module_path not in sys.path:
                sys.path.insert(0, module_path)
            
            # Import or reload module
            if module_name in sys.modules:
                module = importlib.reload(sys.modules[module_name])
            else:
                module = importlib.import_module(module_name)
            
            # Late-bind: rebind all exported callables in registry
            for attr_name in dir(module):
                if attr_name.startswith('_'):
                    continue
                attr = getattr(module, attr_name)
                if callable(attr):
                    registry_key = f"{module_name}.{attr_name}"
                    self.registry[registry_key] = attr
                    
            self.module_cache[module_name] = module
            print(f"[HOT-RELOAD] {module_name} → {len([k for k in self.registry if k.startswith(module_name)])} bindings updated")
            
        except Exception as e:
            print(f"[HOT-RELOAD-ERROR] {module_name}: {e}")

def start_hot_reloader(watch_dir: str, registry: Dict[str, Callable]):
    handler = ModuleHotReloader(registry)
    observer = Observer()
    observer.schedule(handler, watch_dir, recursive=True)
    observer.start()
    return observer

# Global registry for late-bound message passing
ALTHEA_RUNTIME_REGISTRY = {}

if __name__ == "__main__":
    watch_path = os.getenv("ALTHEA_MODULE_PATH", "./modules")
    observer = start_hot_reloader(watch_path, ALTHEA_RUNTIME_REGISTRY)
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()