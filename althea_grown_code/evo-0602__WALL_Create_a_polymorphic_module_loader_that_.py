#!/usr/bin/env python3
import json
import sys
import importlib.util
import inspect
import re
from pathlib import Path
from typing import Any, Dict, Optional, Union

class DuckLoader:
    """WALL-style polymorphic module loader - TIMTOWTDI for module discovery"""
    
    def __init__(self, search_paths=[Path("./modules"), Path(".")]):
        self.search_paths = search_paths
        self.registry = {}
    
    def sniff(self, source: Union[str, Path, Dict]) -> Optional[Dict[str, Any]]:
        """Duck-type the source and extract capabilities"""
        # JSON manifest
        if isinstance(source, dict):
            return source
        
        # File path
        path = Path(source) if isinstance(source, str) else source
        
        if path.suffix == ".json":
            with open(path) as f:
                return json.load(f)
        
        # Python module - introspect it
        if path.suffix == ".py":
            spec = importlib.util.spec_from_file_location(path.stem, path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            
            caps = {
                "name": path.stem,
                "type": "python",
                "callable": [],
                "docstring": getattr(module, "__doc__", "")
            }
            
            for name, obj in inspect.getmembers(module):
                if callable(obj) and not name.startswith("_"):
                    caps["callable"].append({
                        "name": name,
                        "sig": str(inspect.signature(obj)) if inspect.isfunction(obj) else "unknown",
                        "doc": getattr(obj, "__doc__", "")
                    })
            
            return caps
        
        # Executable - assume stdin/stdout pipe protocol
        if path.is_file() and path.stat().st_mode & 0o111:
            return {"name": path.stem, "type": "pipe", "path": str(path)}
        
        return None
    
    def load_all(self) -> Dict[str, Any]:
        """Scan paths and discover everything that looks module-ish"""
        for search_path in self.search_paths:
            if not search_path.exists():
                continue
            for candidate in search_path.iterdir():
                caps = self.sniff(candidate)
                if caps:
                    self.registry[caps.get("name", candidate.name)] = caps
        return self.registry
    
    def __repr__(self):
        return f"DuckLoader({len(self.registry)} modules: {list(self.registry.keys())})"

if __name__ == "__main__":
    loader = DuckLoader()
    loader.load_all()
    json.dump(loader.registry, sys.stdout, indent=2)