#!/usr/bin/env python3
"""Runtime Module Registry - Late-binding capability swapping"""

import inspect
import importlib
import sys
from typing import Any, Callable, Dict, Protocol
from dataclasses import dataclass, field
from datetime import datetime


class ModuleProtocol(Protocol):
    """Message-passing interface for swappable modules"""
    def handle(self, message: str, context: Dict[str, Any]) -> Any: ...
    def describe(self) -> str: ...


@dataclass
class ModuleSlot:
    """Late-bound module container"""
    name: str
    protocol: type
    instance: Any = None
    version: str = "0.0.0"
    loaded_at: datetime = field(default_factory=datetime.now)
    
    def send(self, message: str, **context) -> Any:
        """Message-passing to bound module"""
        if not self.instance:
            raise RuntimeError(f"Slot '{self.name}' unbound")
        return self.instance.handle(message, context)
    
    def hot_swap(self, new_instance: Any, new_version: str):
        """Runtime replacement without restart"""
        if not isinstance(new_instance, self.protocol):
            raise TypeError(f"Instance violates protocol {self.protocol.__name__}")
        old = self.instance
        self.instance = new_instance
        self.version = new_version
        self.loaded_at = datetime.now()
        return old


class RuntimeRegistry:
    """Central registry for hot-swappable capabilities"""
    
    def __init__(self):
        self.slots: Dict[str, ModuleSlot] = {}
        self.message_log: list = []
    
    def register_slot(self, name: str, protocol: type, initial: Any = None):
        """Create late-binding slot"""
        slot = ModuleSlot(name=name, protocol=protocol, instance=initial)
        self.slots[name] = slot
        return slot
    
    def swap(self, slot_name: str, new_module: Any, version: str):
        """Hot-swap module at runtime"""
        if slot_name not in self.slots:
            raise KeyError(f"Unknown slot: {slot_name}")
        return self.slots[slot_name].hot_swap(new_module, version)
    
    def send_to(self, slot_name: str, message: str, **context) -> Any:
        """Send message to module in slot"""
        result = self.slots[slot_name].send(message, **context)
        self.message_log.append((datetime.now(), slot_name, message))
        return result
    
    def introspect(self) -> Dict[str, Any]:
        """Runtime system state"""
        return {
            name: {
                "version": slot.version,
                "loaded_at": slot.loaded_at.isoformat(),
                "description": slot.instance.describe() if slot.instance else None
            }
            for name, slot in self.slots.items()
        }


# Global runtime registry for Althea's live system
ALTHEA_RUNTIME = RuntimeRegistry()