#!/usr/bin/env python3
import json
from typing import Any, Callable, Dict, Optional
from datetime import datetime

class ModuleMessage:
    def __init__(self, selector: str, payload: Any, context: Dict[str, Any]):
        self.selector = selector
        self.payload = payload
        self.context = context
        self.timestamp = datetime.utcnow().isoformat()

class LiveModule:
    def __init__(self, name: str, handler: Callable):
        self.name = name
        self.handler = handler
        self.version = 0
        self.message_count = 0
    
    def send(self, message: ModuleMessage) -> Any:
        self.message_count += 1
        return self.handler(message)
    
    def hot_swap(self, new_handler: Callable):
        self.version += 1
        self.handler = new_handler

class RuntimeModuleRegistry:
    def __init__(self):
        self.modules: Dict[str, LiveModule] = {}
        self.interceptors: list[Callable] = []
    
    def register(self, name: str, handler: Callable) -> LiveModule:
        module = LiveModule(name, handler)
        self.modules[name] = module
        return module
    
    def swap(self, name: str, new_handler: Callable) -> bool:
        if name in self.modules:
            self.modules[name].hot_swap(new_handler)
            return True
        return False
    
    def send_to(self, name: str, selector: str, payload: Any, context: Optional[Dict] = None) -> Any:
        if name not in self.modules:
            return {"error": "module_not_found", "name": name}
        
        msg = ModuleMessage(selector, payload, context or {})
        
        for interceptor in self.interceptors:
            msg = interceptor(msg) or msg
        
        return self.modules[name].send(msg)
    
    def introspect(self) -> Dict[str, Any]:
        return {
            name: {
                "version": mod.version,
                "messages": mod.message_count,
                "bound": True
            }
            for name, mod in self.modules.items()
        }
    
    def add_interceptor(self, interceptor: Callable):
        self.interceptors.append(interceptor)

if __name__ == "__main__":
    registry = RuntimeModuleRegistry()
    
    def semantic_inverter(msg: ModuleMessage) -> Any:
        return {"inverted": not msg.payload.get("value", False)}
    
    registry.register("semantic-inversion", semantic_inverter)
    result = registry.send_to("semantic-inversion", "invert", {"value": True})
    print(json.dumps(registry.introspect(), indent=2))