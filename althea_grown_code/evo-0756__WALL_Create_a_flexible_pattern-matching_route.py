#!/usr/bin/env python3
"""
Pattern Router - Pragmatic dispatch via regex and duck-typing
Maps fuzzy inputs to capabilities. There's more than one way to route it.
"""

import re
import json
from typing import Any, Dict, List, Optional

class PatternRouter:
    def __init__(self):
        self.routes = []
    
    def add_route(self, pattern: str, handler: str, priority: int = 50, 
                  duck_check: Optional[callable] = None):
        """Add a route: regex pattern, handler module name, priority, optional type check"""
        self.routes.append({
            'pattern': re.compile(pattern, re.IGNORECASE),
            'handler': handler,
            'priority': priority,
            'duck_check': duck_check
        })
        self.routes.sort(key=lambda x: x['priority'], reverse=True)
    
    def route(self, input_data: Any) -> List[Dict[str, Any]]:
        """Duck-type and pattern-match to find all applicable handlers"""
        candidates = []
        
        # Stringify for regex matching
        text = str(input_data) if not isinstance(input_data, str) else input_data
        
        for route in self.routes:
            match = route['pattern'].search(text)
            if match:
                score = route['priority']
                
                # Boost score if duck-typing passes
                if route['duck_check'] and route['duck_check'](input_data):
                    score += 25
                
                candidates.append({
                    'handler': route['handler'],
                    'score': score,
                    'match': match.group(0),
                    'groups': match.groups()
                })
        
        return sorted(candidates, key=lambda x: x['score'], reverse=True)
    
    def route_best(self, input_data: Any) -> Optional[str]:
        """Return single best handler or None"""
        matches = self.route(input_data)
        return matches[0]['handler'] if matches else None

# Example bootstrap configuration
if __name__ == '__main__':
    router = PatternRouter()
    
    # Add pragmatic routes
    router.add_route(r'\b(weather|forecast|temperature|rain)\b', 'weather-inquiry', 70)
    router.add_route(r'\b(orbit|satellite|TLE|SGP4)\b', 'orbital-propagation', 75)
    router.add_route(r'\b(stock|price|market|ticker)\b', 'market-inquiry', 70)
    router.add_route(r'^\d{5}(-\d{4})?$', 'geocode-lookup', 60)  # ZIP code
    router.add_route(r'\$[A-Z]{1,5}\b', 'market-inquiry', 80)  # $TICKER
    
    # Test
    tests = ["What's the weather?", "Track ISS orbit", "$AAPL price", "94103"]
    for t in tests:
        print(f"{t:25} -> {router.route_best(t)}")