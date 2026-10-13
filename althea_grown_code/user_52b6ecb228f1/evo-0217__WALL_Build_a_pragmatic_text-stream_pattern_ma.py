#!/usr/bin/env python3
import sys
import re
import json

class StreamPatternMatcher:
    def __init__(self):
        self.handlers = {}
        self.transformers = []
    
    def register(self, pattern, handler):
        """Duck-typed handler registration - anything callable works."""
        self.handlers[pattern] = handler
        return self
    
    def pipe(self, transformer):
        """Chain transformers TIMTOWTDI style."""
        self.transformers.append(transformer)
        return self
    
    def match_and_transform(self, line):
        """Apply first matching pattern, then pipe through transformers."""
        for pattern, handler in self.handlers.items():
            match = re.search(pattern, line)
            if match:
                result = handler(match, line)
                for transform in self.transformers:
                    result = transform(result)
                return result
        return None

def main():
    matcher = StreamPatternMatcher()
    
    # Register semantic pattern handlers
    matcher.register(
        r'\[(\w+)\s+([^\]]+)\]',
        lambda m, l: {"type": m.group(1), "path": m.group(2), "raw": l}
    )
    matcher.register(
        r'INTENT:\s*(.+)',
        lambda m, l: {"type": "INTENT", "content": m.group(1).strip()}
    )
    matcher.register(
        r'→',
        lambda m, l: {"type": "TRANSITION", "content": l.strip()}
    )
    
    # Pipe through JSON serializer
    matcher.pipe(lambda obj: json.dumps(obj) if obj else None)
    
    # Stream processing
    for line in sys.stdin:
        result = matcher.match_and_transform(line.rstrip())
        if result:
            print(result, flush=True)

if __name__ == "__main__":
    main()