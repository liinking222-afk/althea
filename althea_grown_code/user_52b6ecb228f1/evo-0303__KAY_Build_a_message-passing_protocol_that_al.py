import asyncio
from typing import Callable, Any, Dict, List
from dataclasses import dataclass, field
from collections import defaultdict
import time

@dataclass
class Message:
    selector: str
    payload: Any
    timestamp: float = field(default_factory=time.time)
    
@dataclass
class Handler:
    func: Callable
    priority: int = 0
    active: bool = True

class MessagePassingRuntime:
    def __init__(self):
        self.handlers: Dict[str, List[Handler]] = defaultdict(list)
        self.queue: asyncio.Queue = asyncio.Queue()
        self.running = False
        
    def register(self, selector: str, func: Callable, priority: int = 0):
        """Late-bind a handler to a message selector at runtime"""
        handler = Handler(func=func, priority=priority)
        self.handlers[selector].append(handler)
        self.handlers[selector].sort(key=lambda h: h.priority, reverse=True)
        return handler
    
    def unregister(self, selector: str, handler: Handler):
        """Remove a handler while system is running"""
        if selector in self.handlers:
            self.handlers[selector] = [h for h in self.handlers[selector] if h != handler]
    
    def replace(self, selector: str, old_func: Callable, new_func: Callable):
        """Hot-swap a handler implementation"""
        for handler in self.handlers.get(selector, []):
            if handler.func == old_func:
                handler.func = new_func
                return True
        return False
    
    async def send(self, selector: str, payload: Any):
        """Send a message into the system"""
        await self.queue.put(Message(selector=selector, payload=payload))
    
    async def dispatch(self, message: Message):
        """Execute all active handlers for a selector"""
        results = []
        for handler in self.handlers.get(message.selector, []):
            if handler.active:
                try:
                    result = await handler.func(message.payload) if asyncio.iscoroutinefunction(handler.func) else handler.func(message.payload)
                    results.append(result)
                except Exception as e:
                    results.append({"error": str(e)})
        return results
    
    async def run(self):
        """Main event loop - processes messages continuously"""
        self.running = True
        while self.running:
            try:
                message = await asyncio.wait_for(self.queue.get(), timeout=0.1)
                await self.dispatch(message)
            except asyncio.TimeoutError:
                continue
    
    def stop(self):
        self.running = False

runtime = MessagePassingRuntime()