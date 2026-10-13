import inspect
from typing import Any, Callable, Dict, Optional
from dataclasses import dataclass, field
from datetime import datetime

@dataclass
class Message:
    selector: str
    payload: Dict[str, Any]
    timestamp: float = field(default_factory=lambda: datetime.now().timestamp())

class LateBindingDispatcher:
    def __init__(self):
        self._receivers: Dict[str, Callable] = {}
        self._message_log: list[Message] = []
        self._intercepts: Dict[str, Callable] = {}
    
    def register_receiver(self, selector: str, handler: Callable) -> None:
        """Register or replace a message handler at runtime."""
        self._receivers[selector] = handler
    
    def unregister_receiver(self, selector: str) -> Optional[Callable]:
        """Remove a handler, returning it for potential restoration."""
        return self._receivers.pop(selector, None)
    
    def send(self, selector: str, **payload) -> Any:
        """Send message with late binding—handler resolved at call time."""
        msg = Message(selector=selector, payload=payload)
        self._message_log.append(msg)
        
        if selector in self._intercepts:
            return self._intercepts[selector](msg, self._receivers.get(selector))
        
        if selector not in self._receivers:
            return self._handle_unknown(msg)
        
        handler = self._receivers[selector]
        sig = inspect.signature(handler)
        
        if 'message' in sig.parameters:
            return handler(message=msg)
        else:
            return handler(**payload)
    
    def intercept(self, selector: str, wrapper: Callable) -> None:
        """Wrap existing handlers without replacing them."""
        self._intercepts[selector] = wrapper
    
    def replay_to(self, new_receiver: str, old_receiver: str) -> int:
        """Replay messages sent to old_receiver through new_receiver."""
        count = 0
        for msg in self._message_log:
            if msg.selector == old_receiver:
                self.send(new_receiver, **msg.payload)
                count += 1
        return count
    
    def _handle_unknown(self, msg: Message) -> None:
        """Default handler for unknown selectors—can be overridden."""
        if 'doesNotUnderstand' in self._receivers:
            return self._receivers['doesNotUnderstand'](msg)
        return None

global_dispatcher = LateBindingDispatcher()