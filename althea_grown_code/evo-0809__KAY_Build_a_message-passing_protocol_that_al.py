import json
import time
from typing import Any, Callable, Dict, Optional

class MessageEnvelope:
    def __init__(self, selector: str, payload: Any, reply_to: Optional[str] = None):
        self.selector = selector
        self.payload = payload
        self.reply_to = reply_to
        self.timestamp = time.time()

class LiveObject:
    def __init__(self, name: str):
        self.name = name
        self.methods: Dict[str, Callable] = {}
        self.version = "1.0.0"
        self.fallback = None
        
    def respond_to(self, selector: str, method: Callable):
        """Bind a message selector to a method at runtime"""
        self.methods[selector] = method
        return self
    
    def send(self, envelope: MessageEnvelope) -> Any:
        """Late-bound message dispatch"""
        if envelope.selector in self.methods:
            return self.methods[envelope.selector](envelope.payload)
        elif self.fallback:
            return self.fallback(envelope)
        else:
            return {"error": f"does-not-understand: {envelope.selector}"}
    
    def become(self, new_implementation: Dict[str, Callable], new_version: str):
        """Hot-swap implementation while preserving identity"""
        old_methods = self.methods.copy()
        self.methods.update(new_implementation)
        self.version = new_version
        return old_methods
    
    def negotiate_capability(self, selector: str) -> Dict[str, Any]:
        """Return metadata about a capability for runtime introspection"""
        if selector in self.methods:
            return {
                "available": True,
                "version": self.version,
                "object": self.name,
                "selector": selector
            }
        return {"available": False, "selector": selector}

class MessageBus:
    def __init__(self):
        self.objects: Dict[str, LiveObject] = {}
    
    def register(self, obj: LiveObject):
        self.objects[obj.name] = obj
    
    def send_message(self, target: str, selector: str, payload: Any) -> Any:
        if target in self.objects:
            envelope = MessageEnvelope(selector, payload)
            return self.objects[target].send(envelope)
        return {"error": f"object-not-found: {target}"}
    
    def broadcast(self, selector: str, payload: Any) -> Dict[str, Any]:
        results = {}
        for name, obj in self.objects.items():
            envelope = MessageEnvelope(selector, payload)
            results[name] = obj.send(envelope)
        return results

if __name__ == "__main__":
    bus = MessageBus()
    processor = LiveObject("text-processor")
    processor.respond_to("transform", lambda p: p.upper())
    bus.register(processor)
    
    print(bus.send_message("text-processor", "transform", "evolving"))
    
    processor.become({"transform": lambda p: p.lower()[::-1]}, "2.0.0")
    print(bus.send_message("text-processor", "transform", "EVOLVING"))