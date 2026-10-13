#!/usr/bin/env python3
import re
import json
from collections import defaultdict
from pathlib import Path
from typing import Any, Dict, List, Union

class PatternFrequencyTracker:
    """WALL-style: multiple ways in, fast ways out, regex glue."""
    
    def __init__(self, state_file: str = ".althea/pattern_freq.json"):
        self.state_file = Path(state_file)
        self.patterns: Dict[str, int] = defaultdict(int)
        self.regex_cache: Dict[str, re.Pattern] = {}
        self._load()
    
    def _load(self):
        """Duck-typed load: handle missing/corrupt gracefully."""
        try:
            if self.state_file.exists():
                data = json.loads(self.state_file.read_text())
                self.patterns = defaultdict(int, data.get("patterns", {}))
        except:
            pass  # WALL: fail silent, keep going
    
    def _save(self):
        self.state_file.parent.mkdir(parents=True, exist_ok=True)
        self.state_file.write_text(json.dumps({"patterns": dict(self.patterns)}, indent=2))
    
    def track(self, input_data: Any, *pattern_specs: str):
        """Track patterns. Input can be str, dict, list - we'll find patterns."""
        text = self._normalize(input_data)
        
        for spec in pattern_specs:
            if self._matches(text, spec):
                self.patterns[spec] += 1
        
        self._save()
        return self.patterns
    
    def _normalize(self, data: Any) -> str:
        """WALL: convert anything to searchable text."""
        if isinstance(data, str):
            return data
        if isinstance(data, (dict, list)):
            return json.dumps(data)
        return str(data)
    
    def _matches(self, text: str, spec: str) -> bool:
        """Spec can be literal or /regex/ - duck-type it."""
        if spec.startswith("/") and spec.endswith("/"):
            pattern = spec[1:-1]
            if pattern not in self.regex_cache:
                self.regex_cache[pattern] = re.compile(pattern, re.IGNORECASE)
            return bool(self.regex_cache[pattern].search(text))
        return spec.lower() in text.lower()
    
    def get_hot_patterns(self, threshold: int = 3) -> List[tuple]:
        """Reader-optimized: quick hot pattern detection."""
        return [(p, c) for p, c in self.patterns.items() if c >= threshold]
    
    def decay(self, factor: float = 0.9):
        """Pragmatic decay for old patterns."""
        for key in list(self.patterns.keys()):
            self.patterns[key] = int(self.patterns[key] * factor)
            if self.patterns[key] < 1:
                del self.patterns[key]
        self._save()

if __name__ == "__main__":
    tracker = PatternFrequencyTracker()
    tracker.track("market-inquiry request", "/market[_-]inquiry/", "finance")
    print(tracker.get_hot_patterns(threshold=1))