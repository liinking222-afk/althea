#!/usr/bin/env python3
"""
Runtime Message Broker - Kay-style late-binding module communication
Enables runtime introspection and behavior modification through message passing
"""

import json
import inspect
from typing import Any, Callable, Dict, List, Optional
from datetime import datetime


class MessageBroker:
    """Central message-passing hub for inter-module communication"""
    
    def __init__(self):
        self._handlers: Dict[str, List[Callable]] = {}
        self._module_capabilities: Dict[str, Dict[str, Any]] = {}
        self._message_log: List[Dict] = []
    
    def register_capability(self, module_name: str, capability: str, handler: Callable):
        """Register a module capability that can be invoked via message"""
        if capability not in self._handlers:
            self._handlers[capability] = []
        self._handlers[capability].append((module_name, handler))
        
        if module_name not in self._module_capabilities:
            self._module_capabilities[module_name] = {}
        self._module_capabilities[module_name][capability] = {
            "signature": str(inspect.signature(handler)),
            "doc": inspect.getdoc(handler) or ""
        }
    
    def send(self, capability: str, **kwargs) -> List[Any]:
        """Send message to all handlers of a capability"""
        results = []
        if capability in self._handlers:
            for module_name, handler in self._handlers[capability]:
                try:
                    result = handler(**kwargs)
                    results.append({"module": module_name, "result": result})
                    self._log_message(capability, module_name, kwargs, result)
                except Exception as e:
                    results.append({"module": module_name, "error": str(e)})
        return results
    
    def introspect(self, module_name: Optional[str] = None) -> Dict:
        """Query available capabilities across all or specific modules"""
        if module_name:
            return self._module_capabilities.get(module_name, {})
        return self._module_capabilities
    
    def modify_handler(self, capability: str, module_name: str, new_handler: Callable):
        """Runtime replacement of capability handler - Kay's runtime malleability"""
        if capability in self._handlers:
            for i, (mod, _) in enumerate(self._handlers[capability]):
                if mod == module_name:
                    self._handlers[capability][i] = (module_name, new_handler)
                    self._module_capabilities[module_name][capability]["signature"] = str(inspect.signature(new_handler))
                    return True
        return False
    
    def _log_message(self, capability: str, module: str, payload: Dict, result: Any):
        self._message_log.append({
            "timestamp": datetime.utcnow().isoformat(),
            "capability": capability,
            "module": module,
            "payload": payload,
            "result": str(result)[:200]
        })


# Global singleton broker
BROKER = MessageBroker()