#!/usr/bin/env python3
import re
import json
from typing import Any, Callable, Dict, List, Optional

class PolygotMatcher:
    """Duck-typed pattern matcher for heterogeneous module outputs."""
    
    def __init__(self):
        self.matchers: List[tuple[str, Callable[[str], Optional[Dict]]]] = []
        self._register_defaults()
    
    def _register_defaults(self):
        """Register common Althea output patterns."""
        self.matchers.extend([
            ("json", self._match_json),
            ("tle", self._match_tle),
            ("svg", self._match_svg),
            ("module_ref", self._match_module_ref),
            ("fractal_coords", self._match_fractal_coords),
            ("key_value", self._match_key_value),
        ])
    
    def _match_json(self, text: str) -> Optional[Dict]:
        try:
            return {"type": "json", "data": json.loads(text)}
        except: return None
    
    def _match_tle(self, text: str) -> Optional[Dict]:
        lines = text.strip().split('\n')
        if len(lines) >= 2 and re.match(r'^1 \d{5}', lines[-2]) and re.match(r'^2 \d{5}', lines[-1]):
            return {"type": "tle", "lines": lines[-2:], "name": lines[-3] if len(lines) > 2 else ""}
        return None
    
    def _match_svg(self, text: str) -> Optional[Dict]:
        if match := re.search(r'<svg[^>]*>(.*?)</svg>', text, re.DOTALL):
            return {"type": "svg", "content": match.group(0)}
        return None
    
    def _match_module_ref(self, text: str) -> Optional[Dict]:
        if match := re.search(r'/autonomous-([a-z-]+)-(\d+)', text):
            return {"type": "module_ref", "name": match.group(1), "id": match.group(2)}
        return None
    
    def _match_fractal_coords(self, text: str) -> Optional[Dict]:
        pattern = r'(-?\d+\.?\d*)[,\s]+(-?\d+\.?\d*)[,\s]+(\d+\.?\d*)'
        if match := re.search(pattern, text):
            return {"type": "fractal_coords", "center": [float(match.group(1)), float(match.group(2))], "zoom": float(match.group(3))}
        return None
    
    def _match_key_value(self, text: str) -> Optional[Dict]:
        pairs = re.findall(r'(\w+)\s*[:=]\s*([^\n,;]+)', text)
        if pairs:
            return {"type": "key_value", "pairs": dict(pairs)}
        return None
    
    def match(self, text: str) -> List[Dict[str, Any]]:
        """Try all matchers, return all that succeed (TIMTOWTDI)."""
        results = []
        for name, matcher in self.matchers:
            if result := matcher(text):
                result["matcher"] = name
                results.append(result)
        return results
    
    def add_matcher(self, name: str, func: Callable[[str], Optional[Dict]]):
        """Runtime extensibility - add custom matchers on the fly."""
        self.matchers.append((name, func))

if __name__ == "__main__":
    pm = PolygotMatcher()
    test = "/autonomous-fractal-render-3315 at -0.5, 0.0, 2.5"
    print(json.dumps(pm.match(test), indent=2))