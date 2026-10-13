#!/usr/bin/env python3
import importlib
import sys
from typing import Dict, Any, Callable, Optional
from dataclasses import dataclass, field
from datetime import datetime

@dataclass
class ModuleCell:
    """A late-bound cell holding a module reference and its message handler."""
    name: str
    handler: Callable
    version: str
    state: Dict[str, Any] = field(default_factory=dict)
    loaded_at: datetime = field(default_factory=datetime.now)
    
    def send(self, message: str, **kwargs) -> Any:
        """Message-passing interface to module."""
        return self.handler(message, self.state, **kwargs)

class LiveModuleRegistry:
    """Runtime-modifiable module registry with hot-swap capability."""
    
    def __init__(self):
        self.cells: Dict[str, ModuleCell] = {}
        
    def register(self, name: str, handler: Callable, version: str = "1.0.0") -> None:
        """Register or replace a module at runtime."""
        old_state = {}
        if name in self.cells:
            old_cell = self.cells[name]
            old_state = old_cell.send("export_state")
            old_cell.send("teardown")
        
        cell = ModuleCell(name, handler, version)
        if old_state:
            cell.send("import_state", state=old_state)
        self.cells[name] = cell
        
    def send(self, name: str, message: str, **kwargs) -> Any:
        """Send message to registered module."""
        if name not in self.cells:
            raise KeyError(f"Module {name} not registered")
        return self.cells[name].send(message, **kwargs)
    
    def evolve(self, name: str, new_handler: Callable, new_version: str) -> Dict[str, Any]:
        """Hot-swap module with state preservation."""
        old_version = self.cells[name].version if name in self.cells else "none"
        self.register(name, new_handler, new_version)
        return {
            "module": name,
            "transition": f"{old_version} → {new_version}",
            "timestamp": datetime.now().isoformat()
        }
    
    def introspect(self) -> Dict[str, Any]:
        """Query registry state."""
        return {
            name: {
                "version": cell.version,
                "loaded_at": cell.loaded_at.isoformat(),
                "state_keys": list(cell.state.keys())
            }
            for name, cell in self.cells.items()
        }

if __name__ == "__main__":
    registry = LiveModuleRegistry()
    print("Live module registry initialized. All objects message-passing enabled.")