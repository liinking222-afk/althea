#!/usr/bin/env python3
import re
import json
import yaml
from pathlib import Path
from typing import Any, Iterator

class ModuleRegistry:
    """WALL-style registry: read anything, query flexibly, optimize for both writer and reader."""
    
    def __init__(self, source: str | dict | Path):
        self.data = self._slurp(source)
    
    def _slurp(self, source: Any) -> dict:
        """There's more than one way to load it."""
        if isinstance(source, dict):
            return source
        if isinstance(source, Path):
            source = source.read_text()
        if isinstance(source, str):
            # Try JSON first
            try:
                return json.loads(source)
            except json.JSONDecodeError:
                pass
            # Try YAML
            try:
                return yaml.safe_load(source)
            except yaml.YAMLError:
                pass
            # Fall back to key-value parsing
            return self._parse_plaintext(source)
        return {}
    
    def _parse_plaintext(self, text: str) -> dict:
        """Parse loose key:value or key=value format."""
        result = {}
        for line in text.splitlines():
            match = re.match(r'^\s*([^:=]+)[:=]\s*(.+)$', line)
            if match:
                result[match.group(1).strip()] = match.group(2).strip()
        return result
    
    def grep(self, pattern: str, field: str = None) -> Iterator[tuple[str, Any]]:
        """Regex search across keys or specific field values."""
        regex = re.compile(pattern, re.IGNORECASE)
        for key, value in self.data.items():
            if field is None:
                if regex.search(key):
                    yield (key, value)
            elif isinstance(value, dict) and field in value:
                if regex.search(str(value[field])):
                    yield (key, value)
    
    def __getitem__(self, key: str) -> Any:
        return self.data[key]
    
    def __contains__(self, key: str) -> bool:
        return key in self.data
    
    def keys(self):
        return self.data.keys()
    
    def dump(self) -> str:
        """Export as pipe-friendly text."""
        return '\n'.join(f"{k}={v}" for k, v in self.data.items())