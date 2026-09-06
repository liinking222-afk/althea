#!/usr/bin/env python3
"""
Runtime Message Router - Late-binding capability dispatcher
Enables Althea to route messages to capabilities discovered at runtime
"""

import re
import json
from typing import Dict, List, Callable, Any, Optional
from dataclasses import dataclass, asdict

@dataclass
class CapabilityMessage:
    intent: str
    payload: Dict[str, Any]
    context: Optional[Dict[str, Any]] = None

@dataclass
class CapabilityEndpoint:
    pattern: str
    handler: str
    priority: int = 50

class RuntimeMessageRouter:
    def __init__(self):
        self.endpoints: List[CapabilityEndpoint] = []
        self.handlers: Dict[str, Callable] = {}
        self.message_log: List[Dict] = []
    
    def register_capability(self, pattern: str, handler: Callable, priority: int = 50):
        """Late-bind a capability handler at runtime"""
        endpoint = CapabilityEndpoint(pattern, handler.__name__, priority)
        self.endpoints.append(endpoint)
        self.handlers[handler.__name__] = handler
        self.endpoints.sort(key=lambda e: e.priority, reverse=True)
    
    def dispatch(self, message: CapabilityMessage) -> Any:
        """Message-passing dispatch to appropriate handler"""
        self.message_log.append({"intent": message.intent, "timestamp": "runtime"})
        
        for endpoint in self.endpoints:
            if re.search(endpoint.pattern, message.intent, re.IGNORECASE):
                handler = self.handlers.get(endpoint.handler)
                if handler:
                    return handler(message.payload, message.context)
        
        return {"error": "no_handler", "intent": message.intent}
    
    def introspect(self) -> Dict[str, Any]:
        """Runtime introspection of routing table"""
        return {
            "endpoints": [asdict(e) for e in self.endpoints],
            "handler_count": len(self.handlers),
            "message_count": len(self.message_log)
        }
    
    def rewire(self, old_pattern: str, new_pattern: str):
        """Modify routing while running"""
        for endpoint in self.endpoints:
            if endpoint.pattern == old_pattern:
                endpoint.pattern = new_pattern
                return True
        return False

if __name__ == "__main__":
    router = RuntimeMessageRouter()
    print(json.dumps(router.introspect(), indent=2))