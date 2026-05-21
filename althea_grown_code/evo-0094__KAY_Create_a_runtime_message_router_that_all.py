#!/usr/bin/env python3
"""
runtime_message_router.py - Dynamic late-binding command dispatcher
"""
import inspect
import json
from typing import Callable, Dict, Any, Optional
from datetime import datetime

class MessageRouter:
    def __init__(self):
        self.handlers: Dict[str, Callable] = {}
        self.metadata: Dict[str, Dict[str, Any]] = {}
        self.message_log = []
    
    def bind(self, message_type: str, handler: Callable, meta: Optional[Dict] = None):
        """Late-bind a handler to a message type at runtime"""
        self.handlers[message_type] = handler
        self.metadata[message_type] = {
            "bound_at": datetime.now().isoformat(),
            "signature": str(inspect.signature(handler)),
            "source": inspect.getsource(handler) if not inspect.isbuiltin(handler) else "<builtin>",
            **(meta or {})
        }
        return self
    
    def unbind(self, message_type: str):
        """Remove binding while running"""
        self.handlers.pop(message_type, None)
        self.metadata.pop(message_type, None)
        return self
    
    def send(self, message_type: str, payload: Any = None) -> Any:
        """Send message to bound handler"""
        entry = {
            "type": message_type,
            "timestamp": datetime.now().isoformat(),
            "payload": payload
        }
        self.message_log.append(entry)
        
        if message_type not in self.handlers:
            return {"error": f"no_handler_for_{message_type}", "available": list(self.handlers.keys())}
        
        handler = self.handlers[message_type]
        result = handler(payload) if payload is not None else handler()
        entry["result"] = result
        return result
    
    def introspect(self) -> Dict[str, Any]:
        """Examine current bindings"""
        return {
            "handlers": list(self.handlers.keys()),
            "metadata": self.metadata,
            "message_count": len(self.message_log)
        }
    
    def rebind_from_source(self, message_type: str, source_code: str):
        """Redefine handler from source at runtime"""
        local_scope = {}
        exec(source_code, globals(), local_scope)
        handler = local_scope.get("handler")
        if handler:
            self.bind(message_type, handler, {"rebound": True})
        return self

# Global singleton router
ROUTER = MessageRouter()

if __name__ == "__main__":
    ROUTER.bind("ping", lambda: "pong")
    ROUTER.bind("echo", lambda x: x)
    print(ROUTER.send("ping"))
    print(ROUTER.introspect())