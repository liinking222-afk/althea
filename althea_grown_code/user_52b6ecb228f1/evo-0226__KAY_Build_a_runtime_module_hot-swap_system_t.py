#!/usr/bin/env python3
import inspect
import threading
from typing import Any, Callable, Dict, Optional
from collections import defaultdict
from dataclasses import dataclass, field

@dataclass
class MessageContext:
    sender: str
    payload: Any
    version: str
    continuation: Optional[Callable] = None

class ModuleCell:
    def __init__(self, name: str, handler: Callable):
        self.name = name
        self.version = 1
        self.handler = handler
        self.lock = threading.RLock()
        self.inflight: Dict[int, MessageContext] = {}
        
    def send(self, ctx: MessageContext) -> Any:
        with self.lock:
            ctx_id = id(ctx)
            self.inflight[ctx_id] = ctx
            try:
                result = self.handler(ctx)
                return result
            finally:
                self.inflight.pop(ctx_id, None)
    
    def hot_swap(self, new_handler: Callable) -> int:
        with self.lock:
            self.handler = new_handler
            self.version += 1
            for ctx in self.inflight.values():
                if ctx.continuation:
                    ctx.continuation(new_handler, ctx)
            return self.version

class RuntimeMalleable:
    def __init__(self):
        self.cells: Dict[str, ModuleCell] = {}
        self.dispatch_lock = threading.RLock()
        
    def register(self, name: str, handler: Callable) -> ModuleCell:
        with self.dispatch_lock:
            cell = ModuleCell(name, handler)
            self.cells[name] = cell
            return cell
    
    def send_to(self, target: str, payload: Any, sender: str = "system") -> Any:
        cell = self.cells.get(target)
        if not cell:
            raise KeyError(f"Module {target} not found")
        ctx = MessageContext(sender=sender, payload=payload, version=f"v{cell.version}")
        return cell.send(ctx)
    
    def evolve(self, target: str, new_handler: Callable) -> Dict[str, Any]:
        with self.dispatch_lock:
            cell = self.cells.get(target)
            if not cell:
                raise KeyError(f"Module {target} not found")
            old_version = cell.version
            new_version = cell.hot_swap(new_handler)
            return {
                "module": target,
                "old_version": old_version,
                "new_version": new_version,
                "inflight_preserved": len(cell.inflight)
            }

_RUNTIME = RuntimeMalleable()

def module(name: str):
    def decorator(func: Callable):
        _RUNTIME.register(name, func)
        return func
    return decorator

def evolve_module(name: str, new_impl: Callable):
    return _RUNTIME.evolve(name, new_impl)

def send_message(target: str, payload: Any, sender: str = "system"):
    return _RUNTIME.send_to(target, payload, sender)