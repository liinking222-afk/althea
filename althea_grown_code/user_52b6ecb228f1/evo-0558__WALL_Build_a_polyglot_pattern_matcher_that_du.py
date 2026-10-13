#!/usr/bin/env python3
import re
import json
from typing import Any, Union, List, Dict

class PolyglotExtractor:
    """WALL-style pattern matcher: there's more than one way to extract it."""
    
    def __init__(self):
        self.patterns = {}
    
    def register(self, name: str, pattern: Union[str, dict]):
        """Register a pattern by name - auto-detects type."""
        self.patterns[name] = pattern
    
    def extract(self, data: Any, pattern: Union[str, dict]) -> List[Any]:
        """Extract using whatever pattern fits the data."""
        # Duck-type the data
        if isinstance(data, str):
            return self._extract_from_text(data, pattern)
        elif isinstance(data, (dict, list)):
            return self._extract_from_json(data, pattern)
        else:
            return self._extract_from_text(str(data), pattern)
    
    def _extract_from_text(self, text: str, pattern: Union[str, dict]) -> List[Any]:
        """Regex-first for text."""
        if isinstance(pattern, str):
            matches = re.findall(pattern, text, re.MULTILINE | re.DOTALL)
            return matches if matches else []
        elif isinstance(pattern, dict) and 'regex' in pattern:
            flags = re.MULTILINE | re.DOTALL
            if pattern.get('ignorecase'):
                flags |= re.IGNORECASE
            matches = re.findall(pattern['regex'], text, flags)
            return matches
        return []
    
    def _extract_from_json(self, data: Union[dict, list], pattern: Union[str, dict]) -> List[Any]:
        """JSONPath-like extraction with wildcards."""
        if isinstance(pattern, str):
            return self._jsonpath_walk(data, pattern.split('.'))
        return []
    
    def _jsonpath_walk(self, data: Any, path: List[str]) -> List[Any]:
        """Walk JSON structure - handles wildcards and array notation."""
        if not path:
            return [data]
        
        key = path[0]
        rest = path[1:]
        results = []
        
        if key == '*':
            if isinstance(data, dict):
                for v in data.values():
                    results.extend(self._jsonpath_walk(v, rest))
            elif isinstance(data, list):
                for item in data:
                    results.extend(self._jsonpath_walk(item, rest))
        elif key.endswith('[]'):
            actual_key = key[:-2]
            if isinstance(data, dict) and actual_key in data:
                if isinstance(data[actual_key], list):
                    for item in data[actual_key]:
                        results.extend(self._jsonpath_walk(item, rest))
        else:
            if isinstance(data, dict) and key in data:
                results.extend(self._jsonpath_walk(data[key], rest))
        
        return results if results else []

# Module exports
_extractor = PolyglotExtractor()
extract = _extractor.extract
register = _extractor.register