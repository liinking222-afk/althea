#!/usr/bin/env python3
import re
import sys
from typing import Callable, Any, Iterator

class PipeFilter:
    """Pragmatic stream transformer: regex, lambdas, whatever works."""
    
    def __init__(self, data: Any = None):
        self.data = data if data is not None else sys.stdin
    
    def __or__(self, other: Callable) -> 'PipeFilter':
        """Overload | for Unix-style piping."""
        return PipeFilter(other(self._stream()))
    
    def _stream(self) -> Iterator[str]:
        """Duck-type the data: file, list, string, whatever."""
        if hasattr(self.data, 'read'):
            yield from self.data
        elif isinstance(self.data, str):
            yield from self.data.splitlines(keepends=True)
        elif hasattr(self.data, '__iter__'):
            yield from self.data
        else:
            yield str(self.data)
    
    def collect(self) -> list:
        """Materialize the stream."""
        return list(self._stream())
    
    def print(self):
        """Side effect: print stream."""
        for line in self._stream():
            print(line, end='')
        return self

def grep(pattern: str, flags: int = 0) -> Callable:
    """Filter lines matching regex."""
    rx = re.compile(pattern, flags)
    def _filter(stream: Iterator[str]) -> Iterator[str]:
        return (line for line in stream if rx.search(line))
    return _filter

def sed(pattern: str, replacement: str, flags: int = 0) -> Callable:
    """Transform lines via regex substitution."""
    rx = re.compile(pattern, flags)
    def _transform(stream: Iterator[str]) -> Iterator[str]:
        return (rx.sub(replacement, line) for line in stream)
    return _transform

def map_fn(fn: Callable[[str], str]) -> Callable:
    """Apply arbitrary function to each line."""
    def _map(stream: Iterator[str]) -> Iterator[str]:
        return (fn(line) for line in stream)
    return _map

def head(n: int = 10) -> Callable:
    """Take first n lines."""
    def _head(stream: Iterator[str]) -> Iterator[str]:
        for i, line in enumerate(stream):
            if i >= n:
                break
            yield line
    return _head

# Example usage pattern:
# PipeFilter(data) | grep(r'\[AUTOSYNTH') | sed(r'AUTOSYNTH', 'SYNTH') | head(5) | collect()