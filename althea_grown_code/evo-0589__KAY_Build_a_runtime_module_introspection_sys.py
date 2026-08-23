import inspect
import importlib
import sys
from typing import Any, Dict, List, Callable, Optional
from pathlib import Path

class RuntimeModuleIntrospector:
    """Late-binding module inspection and hot-swap capability"""
    
    def __init__(self):
        self.module_registry: Dict[str, Any] = {}
        self.method_cache: Dict[str, Callable] = {}
        
    def register_module(self, name: str, module: Any) -> None:
        """Register a module for runtime introspection"""
        self.module_registry[name] = module
        self._invalidate_cache(name)
    
    def introspect_module(self, name: str) -> Dict[str, Any]:
        """Examine module structure at runtime"""
        if name not in self.module_registry:
            return {}
        
        module = self.module_registry[name]
        return {
            'methods': [m for m in dir(module) if callable(getattr(module, m)) and not m.startswith('_')],
            'attributes': [a for a in dir(module) if not callable(getattr(module, a)) and not a.startswith('_')],
            'source': inspect.getsource(module) if hasattr(module, '__file__') else None,
            'docstring': inspect.getdoc(module),
            'signature_map': {m: str(inspect.signature(getattr(module, m))) 
                            for m in dir(module) 
                            if callable(getattr(module, m)) and not m.startswith('_')}
        }
    
    def send_message(self, module_name: str, method_name: str, *args, **kwargs) -> Any:
        """Message-passing interface to any registered module"""
        cache_key = f"{module_name}.{method_name}"
        
        if cache_key not in self.method_cache:
            if module_name not in self.module_registry:
                raise ValueError(f"Module {module_name} not registered")
            module = self.module_registry[module_name]
            if not hasattr(module, method_name):
                raise AttributeError(f"Module {module_name} has no method {method_name}")
            self.method_cache[cache_key] = getattr(module, method_name)
        
        return self.method_cache[cache_key](*args, **kwargs)
    
    def hot_reload(self, module_path: str) -> str:
        """Reload a module from disk without restarting"""
        module_name = Path(module_path).stem
        
        if module_name in sys.modules:
            module = importlib.reload(sys.modules[module_name])
        else:
            spec = importlib.util.spec_from_file_location(module_name, module_path)
            module = importlib.util.module_from_spec(spec)
            sys.modules[module_name] = module
            spec.loader.exec_module(module)
        
        self.register_module(module_name, module)
        return f"Reloaded {module_name} at runtime"
    
    def _invalidate_cache(self, module_name: str) -> None:
        """Clear method cache for a module"""
        self.method_cache = {k: v for k, v in self.method_cache.items() 
                            if not k.startswith(f"{module_name}.")}
    
    def list_capabilities(self) -> List[str]:
        """Enumerate all callable capabilities across all modules"""
        capabilities = []
        for mod_name, module in self.module_registry.items():
            methods = [m for m in dir(module) if callable(getattr(module, m)) and not m.startswith('_')]
            capabilities.extend([f"{mod_name}.{m}" for m in methods])
        return capabilities

runtime_introspector = RuntimeModuleIntrospector()