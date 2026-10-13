#!/usr/bin/env python3
"""
Runtime Message Router - Late-binding cognitive operation dispatcher
Enables hot-swapping of module implementations during execution
"""

import importlib
import sys
from typing import Dict, Callable, Any, Optional
from pathlib import Path
import json
import hashlib

class MessageRouter:
    def __init__(self):
        self.bindings: Dict[str, Callable] = {}
        self.routing_table: Dict[str, str] = {}
        self.message_log = []
        
    def bind(self, message: str, handler: Callable, version: str = "1.0"):
        """Late-bind a message pattern to a handler"""
        binding_key = f"{message}@{version}"
        self.bindings[binding_key] = handler
        self.routing_table[message] = binding_key
        
    def rebind(self, message: str, new_handler: Callable, version: str):
        """Rebind message to new implementation while running"""
        old_key = self.routing_table.get(message)
        new_key = f"{message}@{version}"
        self.bindings[new_key] = new_handler
        self.routing_table[message] = new_key
        self.message_log.append({
            "rebind": message,
            "from": old_key,
            "to": new_key,
            "hash": hashlib.sha256(str(new_handler.__code__.co_code).encode()).hexdigest()[:8]
        })
        
    def send(self, message: str, *args, **kwargs) -> Any:
        """Send message to currently bound handler"""
        binding_key = self.routing_table.get(message)
        if not binding_key or binding_key not in self.bindings:
            raise KeyError(f"No handler bound for message: {message}")
        return self.bindings[binding_key](*args, **kwargs)
    
    def introspect(self) -> Dict:
        """Return routing state for meta-operations"""
        return {
            "active_bindings": len(self.routing_table),
            "total_handlers": len(self.bindings),
            "rebind_history": len(self.message_log),
            "routes": {msg: key for msg, key in self.routing_table.items()}
        }
    
    def load_handler_from_file(self, message: str, filepath: str, func_name: str, version: str):
        """Dynamically load and bind handler from external module"""
        spec = importlib.util.spec_from_file_location("dynamic_module", filepath)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        handler = getattr(module, func_name)
        self.rebind(message, handler, version)

router = MessageRouter()

if __name__ == "__main__":
    def analyze_v1(text): return f"v1: {len(text)} chars"
    def analyze_v2(text): return f"v2: {len(text.split())} words"
    
    router.bind("analyze", analyze_v1, "1.0")
    print(router.send("analyze", "hello world"))
    router.rebind("analyze", analyze_v2, "2.0")
    print(router.send("analyze", "hello world"))
    print(json.dumps(router.introspect(), indent=2))