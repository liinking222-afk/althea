import json
import time
from typing import Any, Callable, Dict, Optional
from pathlib import Path

class Message:
    def __init__(self, selector: str, args: dict, sender: str = "system"):
        self.selector = selector
        self.args = args
        self.sender = sender
        self.timestamp = time.time()

class Module:
    def __init__(self, name: str, version: str, responders: Dict[str, Callable]):
        self.name = name
        self.version = version
        self.responders = responders
        self.loaded_at = time.time()
    
    def respond_to(self, message: Message) -> Any:
        if message.selector in self.responders:
            return self.responders[message.selector](message.args)
        return {"error": "selector_not_understood", "selector": message.selector}

class RuntimeRegistry:
    def __init__(self, registry_path: str = "/tmp/althea_modules.json"):
        self.modules: Dict[str, Module] = {}
        self.message_queue = []
        self.registry_path = Path(registry_path)
        self.load_registry()
    
    def load_registry(self):
        if self.registry_path.exists():
            with open(self.registry_path, 'r') as f:
                self.metadata = json.load(f)
        else:
            self.metadata = {"modules": {}, "routes": {}}
    
    def register(self, module: Module, hot: bool = True):
        old_version = self.modules.get(module.name)
        self.modules[module.name] = module
        self.metadata["modules"][module.name] = {
            "version": module.version,
            "loaded_at": module.loaded_at,
            "selectors": list(module.responders.keys())
        }
        self.persist()
        if hot and old_version:
            return {"hot_swapped": True, "old": old_version.version, "new": module.version}
        return {"registered": module.name, "version": module.version}
    
    def send(self, module_name: str, selector: str, args: dict) -> Any:
        if module_name not in self.modules:
            return {"error": "module_not_found", "module": module_name}
        message = Message(selector, args)
        return self.modules[module_name].respond_to(message)
    
    def route(self, selector: str, target_module: str):
        self.metadata["routes"][selector] = target_module
        self.persist()
    
    def dispatch(self, selector: str, args: dict) -> Any:
        target = self.metadata["routes"].get(selector)
        if target:
            return self.send(target, selector, args)
        return {"error": "no_route", "selector": selector}
    
    def persist(self):
        with open(self.registry_path, 'w') as f:
            json.dump(self.metadata, f, indent=2)

registry = RuntimeRegistry()