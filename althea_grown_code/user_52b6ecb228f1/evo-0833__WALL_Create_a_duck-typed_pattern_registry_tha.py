#!/usr/bin/env python3
import re
from typing import Callable, Dict, List, Tuple, Any
from dataclasses import dataclass
import json

@dataclass
class PatternHandler:
    pattern: str
    handler_id: str
    module: str
    priority: int = 50
    
    def matches(self, text: str) -> bool:
        return bool(re.search(self.pattern, text, re.IGNORECASE))

class PatternRegistry:
    def __init__(self):
        self.handlers: List[PatternHandler] = []
        
    def register(self, pattern: str, handler_id: str, module: str, priority: int = 50):
        """There's more than one way to register — regex string is enough."""
        self.handlers.append(PatternHandler(pattern, handler_id, module, priority))
        self.handlers.sort(key=lambda h: h.priority, reverse=True)
        
    def unregister(self, handler_id: str):
        self.handlers = [h for h in self.handlers if h.handler_id != handler_id]
        
    def match(self, text: str) -> List[Dict[str, Any]]:
        """Duck-typed matching — returns all handlers that match."""
        matches = []
        for handler in self.handlers:
            if handler.matches(text):
                matches.append({
                    'handler_id': handler.handler_id,
                    'module': handler.module,
                    'pattern': handler.pattern,
                    'priority': handler.priority
                })
        return matches
    
    def export_state(self) -> str:
        """Serialize for persistence or IPC."""
        return json.dumps([
            {'pattern': h.pattern, 'handler_id': h.handler_id, 
             'module': h.module, 'priority': h.priority}
            for h in self.handlers
        ])
    
    def import_state(self, state: str):
        """Load from serialized state."""
        data = json.loads(state)
        for item in data:
            self.register(item['pattern'], item['handler_id'], 
                         item['module'], item.get('priority', 50))

if __name__ == '__main__':
    registry = PatternRegistry()
    registry.register(r'\b(weather|forecast|temperature)\b', 
                     'weather-inquiry', 'autonomous-weather-inquiry', 70)
    registry.register(r'\b(orbit|satellite|tle|sgp4)\b',
                     'orbital-prop', 'autonomous-orbital-propagation', 65)
    
    test = "What's the weather like and can you track satellite orbits?"
    print(json.dumps(registry.match(test), indent=2))