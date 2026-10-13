#!/usr/bin/env python3
import sys
import json
from typing import TextIO, Callable

class StreamFilter:
    """UNIX-style filter for cognitive module output streams"""
    
    @staticmethod
    def grep(pattern: str) -> Callable[[str], str]:
        """Filter lines matching pattern"""
        return lambda line: line if pattern in line else ""
    
    @staticmethod
    def extract_intent() -> Callable[[str], str]:
        """Extract INTENT lines from module output"""
        return lambda line: line if line.startswith("INTENT:") else ""
    
    @staticmethod
    def json_key(key: str) -> Callable[[str], str]:
        """Extract JSON key if line is valid JSON"""
        def extractor(line: str) -> str:
            try:
                data = json.loads(line)
                return str(data.get(key, ""))
            except:
                return ""
        return extractor
    
    @staticmethod
    def count_tokens() -> Callable[[str], str]:
        """Count and emit token count"""
        count = [0]
        def counter(line: str) -> str:
            count[0] += len(line.split())
            return f"{count[0]}" if line else ""
        return counter

def pipe(input_stream: TextIO, *filters: Callable[[str], str]) -> None:
    """Compose filters left-to-right, write to stdout"""
    for line in input_stream:
        result = line.rstrip('\n')
        for f in filters:
            if not result:
                break
            result = f(result)
        if result:
            sys.stdout.write(result + '\n')
            sys.stdout.flush()

if __name__ == "__main__":
    if len(sys.argv) > 1:
        filter_type = sys.argv[1]
        if filter_type == "intent":
            pipe(sys.stdin, StreamFilter.extract_intent())
        elif filter_type == "grep" and len(sys.argv) > 2:
            pipe(sys.stdin, StreamFilter.grep(sys.argv[2]))
        elif filter_type == "json" and len(sys.argv) > 2:
            pipe(sys.stdin, StreamFilter.json_key(sys.argv[2]))
        elif filter_type == "count":
            pipe(sys.stdin, StreamFilter.count_tokens())
    else:
        pipe(sys.stdin)