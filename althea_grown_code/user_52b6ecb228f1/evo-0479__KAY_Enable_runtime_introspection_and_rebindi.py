import inspect
import importlib
import sys
from typing import Any, Callable, Dict, Optional
from dataclasses import dataclass, field
from datetime import datetime

@dataclass
class MessageHandler:
    name: str
    callable: Callable
    signature: inspect.Signature
    bound_at: datetime
    metadata: Dict[str, Any] = field(default_factory=dict)

class RuntimeRegistry:
    """Late-binding message-passing registry for Althea subsystems."""
    
    def __init__(self):
        self._handlers: Dict[str, MessageHandler] = {}
        self._aliases: Dict[str, str] = {}
        self._message_log: list = []
    
    def bind(self, message_name: str, handler: Callable, **metadata) -> None:
        """Bind a handler to a message at runtime."""
        sig = inspect.signature(handler)
        self._handlers[message_name] = MessageHandler(
            name=message_name,
            callable=handler,
            signature=sig,
            bound_at=datetime.utcnow(),
            metadata=metadata
        )
    
    def rebind(self, message_name: str, new_handler: Callable, **metadata) -> MessageHandler:
        """Replace existing handler, returning the old one."""
        old = self._handlers.get(message_name)
        self.bind(message_name, new_handler, **metadata)
        return old
    
    def alias(self, alias: str, canonical: str) -> None:
        """Create message alias for late binding."""
        self._aliases[alias] = canonical
    
    def send(self, message_name: str, *args, **kwargs) -> Any:
        """Send message to bound handler."""
        resolved = self._aliases.get(message_name, message_name)
        handler = self._handlers.get(resolved)
        
        if not handler:
            raise KeyError(f"No handler bound for message: {message_name}")
        
        self._message_log.append((datetime.utcnow(), message_name, resolved))
        return handler.callable(*args, **kwargs)
    
    def introspect(self, message_name: str) -> Optional[MessageHandler]:
        """Inspect handler without invoking."""
        resolved = self._aliases.get(message_name, message_name)
        return self._handlers.get(resolved)
    
    def list_messages(self) -> Dict[str, datetime]:
        """Return all bound messages and their binding times."""
        return {name: h.bound_at for name, h in self._handlers.items()}
    
    def hot_reload_module(self, module_name: str) -> None:
        """Reload a module and rebind its exported handlers."""
        if module_name in sys.modules:
            importlib.reload(sys.modules[module_name])

registry = RuntimeRegistry()