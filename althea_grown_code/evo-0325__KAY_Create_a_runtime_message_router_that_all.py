import asyncio
from typing import Any, Callable, Dict, List, Optional
from dataclasses import dataclass, field
from datetime import datetime

@dataclass
class Message:
    topic: str
    payload: Any
    sender: str
    timestamp: float = field(default_factory=lambda: datetime.now().timestamp())

class MessageRouter:
    def __init__(self):
        self.handlers: Dict[str, List[Callable]] = {}
        self.routes: Dict[str, str] = {}
        self.middleware: List[Callable] = []
        
    def bind(self, topic: str, handler: Callable) -> None:
        """Late-bind a handler to a topic at runtime"""
        if topic not in self.handlers:
            self.handlers[topic] = []
        self.handlers[topic].append(handler)
    
    def unbind(self, topic: str, handler: Callable) -> None:
        """Remove a binding at runtime"""
        if topic in self.handlers:
            self.handlers[topic] = [h for h in self.handlers[topic] if h != handler]
    
    def alias(self, from_topic: str, to_topic: str) -> None:
        """Dynamically reroute messages from one topic to another"""
        self.routes[from_topic] = to_topic
    
    def intercept(self, middleware: Callable) -> None:
        """Add runtime message transformation middleware"""
        self.middleware.append(middleware)
    
    async def send(self, message: Message) -> List[Any]:
        """Send message through dynamically resolved paths"""
        topic = self.routes.get(message.topic, message.topic)
        
        transformed = message
        for mw in self.middleware:
            transformed = await mw(transformed) if asyncio.iscoroutinefunction(mw) else mw(transformed)
            if transformed is None:
                return []
        
        handlers = self.handlers.get(topic, [])
        results = []
        for handler in handlers:
            result = await handler(transformed) if asyncio.iscoroutinefunction(handler) else handler(transformed)
            results.append(result)
        return results
    
    def introspect(self) -> Dict[str, Any]:
        """Runtime reflection of current binding state"""
        return {
            "topics": list(self.handlers.keys()),
            "handler_counts": {t: len(h) for t, h in self.handlers.items()},
            "routes": self.routes.copy(),
            "middleware_count": len(self.middleware)
        }

router = MessageRouter()