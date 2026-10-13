import inspect
import types
from typing import Any, Callable, Dict, List, Optional
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class Message:
    selector: str
    args: tuple
    kwargs: dict
    timestamp: float = field(default_factory=lambda: datetime.now().timestamp())


@dataclass
class ModuleInterface:
    name: str
    methods: Dict[str, Callable]
    version: str
    hot_swap_enabled: bool = True


class RuntimeReflector:
    def __init__(self):
        self.interfaces: Dict[str, ModuleInterface] = {}
        self.message_log: List[Message] = []
        self.method_hooks: Dict[str, List[Callable]] = {}
    
    def register_module(self, name: str, obj: Any, version: str = "1.0.0"):
        methods = {m: getattr(obj, m) for m in dir(obj) 
                   if callable(getattr(obj, m)) and not m.startswith('_')}
        self.interfaces[name] = ModuleInterface(name, methods, version)
        return self
    
    def send_message(self, module: str, selector: str, *args, **kwargs) -> Any:
        msg = Message(selector, args, kwargs)
        self.message_log.append(msg)
        
        if module not in self.interfaces:
            raise ValueError(f"Module {module} not registered")
        
        interface = self.interfaces[module]
        if selector not in interface.methods:
            raise AttributeError(f"Method {selector} not found in {module}")
        
        # Execute pre-hooks
        for hook in self.method_hooks.get(f"{module}.{selector}", []):
            hook(msg)
        
        return interface.methods[selector](*args, **kwargs)
    
    def hot_swap_method(self, module: str, selector: str, new_impl: Callable):
        if module not in self.interfaces:
            raise ValueError(f"Module {module} not registered")
        
        interface = self.interfaces[module]
        interface.methods[selector] = new_impl
        interface.version = f"{interface.version}+swap"
        return True
    
    def add_hook(self, module: str, selector: str, hook: Callable):
        key = f"{module}.{selector}"
        if key not in self.method_hooks:
            self.method_hooks[key] = []
        self.method_hooks[key].append(hook)
    
    def introspect(self, module: str) -> Dict[str, Any]:
        if module not in self.interfaces:
            return {}
        
        interface = self.interfaces[module]
        return {
            "name": interface.name,
            "version": interface.version,
            "methods": list(interface.methods.keys()),
            "hot_swap_enabled": interface.hot_swap_enabled,
            "message_count": sum(1 for m in self.message_log if module in str(m.selector))
        }


REFLECTOR = RuntimeReflector()