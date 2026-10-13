#!/usr/bin/env python3
import re
from typing import Union, List, Dict, Any, Callable, Optional

class FlexPattern:
    """Pragmatic pattern matcher with multiple strategies - TIMTOWTDI"""
    
    def __init__(self, patterns: Union[str, List[str]], flags: int = re.IGNORECASE):
        self.patterns = [patterns] if isinstance(patterns, str) else patterns
        self.compiled = [re.compile(p, flags) for p in self.patterns]
    
    def match(self, text: str) -> Optional[Dict[str, Any]]:
        """Try patterns until one matches - first wins"""
        for regex in self.compiled:
            m = regex.search(text)
            if m:
                return m.groupdict() if m.groupdict() else {"match": m.group(0)}
        return None
    
    def extract_all(self, text: str) -> List[Dict[str, Any]]:
        """Extract all matches across all patterns"""
        results = []
        for regex in self.compiled:
            for m in regex.finditer(text):
                results.append(m.groupdict() if m.groupdict() else {"match": m.group(0)})
        return results
    
    def transform(self, text: str, fn: Callable[[Dict], str]) -> str:
        """Apply transformation function to first match"""
        for regex in self.compiled:
            m = regex.search(text)
            if m:
                groups = m.groupdict() if m.groupdict() else {"match": m.group(0)}
                replacement = fn(groups)
                return text[:m.start()] + replacement + text[m.end():]
        return text

# Prebuilt patterns for common Althea memory parsing
MEMORY_PATTERNS = {
    "evolution": FlexPattern([
        r"\[EVO #(?P<num>\d+) (?P<arch>\w+) v(?P<from>[\d.]+)→(?P<to>[\d.]+)\]",
        r"\[GROWTH /(?P<slug>[\w-]+)\]"
    ]),
    "metric": FlexPattern(r"(?P<name>\w+)[:\s]+(?P<value>[\d.]+)"),
    "command": FlexPattern(r"\[(?P<type>SYSTEM|IMAGINED|GROWTH)\]?\s*(?P<content>.+)"),
    "version": FlexPattern(r"v?(?P<major>\d+)\.(?P<minor>\d+)\.(?P<patch>\d+)"),
}

def parse_memory_entry(entry: str) -> Dict[str, Any]:
    """Duck-typed memory parser - tries all patterns, returns best match"""
    result = {"raw": entry, "type": "unknown"}
    
    for pattern_name, pattern in MEMORY_PATTERNS.items():
        match = pattern.match(entry)
        if match:
            result["type"] = pattern_name
            result.update(match)
            break
    
    return result

if __name__ == "__main__":
    test = "[EVO #325 KAY v1.30.4→1.30.5] Create runtime message router"
    print(parse_memory_entry(test))