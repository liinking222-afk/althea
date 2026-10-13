import json
import inspect
from typing import Callable, Dict, List, Any
from datetime import datetime

class DynamicMessageBus:
    """Late-binding message bus - handlers attach/detach at runtime"""
    
    def __init__(self):
        self.channels: Dict[str, List[Callable]] = {}
        self.message_log: List[Dict[str, Any]] = []
        self.handler_registry: Dict[str, Dict] = {}
    
    def register_channel(self, channel: str) -> None:
        """Create channel dynamically if it doesn't exist"""
        if channel not in self.channels:
            self.channels[channel] = []
    
    def bind(self, channel: str, handler: Callable, handler_id: str = None) -> str:
        """Late-bind a handler to a channel at runtime"""
        self.register_channel(channel)
        
        if handler_id is None:
            handler_id = f"{channel}_{len(self.handler_registry)}"
        
        self.channels[channel].append(handler)
        self.handler_registry[handler_id] = {
            "channel": channel,
            "handler": handler,
            "bound_at": datetime.utcnow().isoformat(),
            "source": inspect.getsource(handler) if not inspect.isbuiltin(handler) else "<builtin>"
        }
        
        return handler_id
    
    def unbind(self, handler_id: str) -> bool:
        """Remove handler by ID while system runs"""
        if handler_id not in self.handler_registry:
            return False
        
        entry = self.handler_registry[handler_id]
        channel = entry["channel"]
        handler = entry["handler"]
        
        if channel in self.channels and handler in self.channels[channel]:
            self.channels[channel].remove(handler)
            del self.handler_registry[handler_id]
            return True
        
        return False
    
    def send(self, channel: str, message: Any) -> List[Any]:
        """Send message to all bound handlers on channel"""
        if channel not in self.channels:
            return []
        
        results = []
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "channel": channel,
            "message": str(message)[:200],
            "handler_count": len(self.channels[channel])
        }
        
        for handler in self.channels[channel]:
            try:
                result = handler(message)
                results.append(result)
            except Exception as e:
                results.append({"error": str(e)})
        
        self.message_log.append(log_entry)
        return results
    
    def introspect(self) -> Dict[str, Any]:
        """Examine runtime state of the message bus"""
        return {
            "channels": list(self.channels.keys()),
            "handlers": {hid: {k: v for k, v in info.items() if k != "handler"} 
                        for hid, info in self.handler_registry.items()},
            "recent_messages": self.message_log[-10:]
        }