#!/usr/bin/env python3
import sys
import re
from typing import Iterator, Callable

def stream_modules(registry_path: str = None) -> Iterator[str]:
    """Emit one module per line: name|version|tags|status"""
    # Simulated - in practice would read from actual registry
    modules = [
        "/autonomous-data-visualization-1791|1.0.0|viz,matplotlib|active",
        "/autonomous-transfer-learning-1775|1.2.1|ml,train|active",
        "/autonomous-semantic-convection|0.9.3|network,emergent|active",
        "/autonomous-orbital-propagation-1729|2.1.0|astro,sgp4|active",
    ]
    for line in modules:
        yield line

def grep(pattern: str) -> Callable[[Iterator[str]], Iterator[str]]:
    """Filter lines matching regex pattern"""
    regex = re.compile(pattern)
    def _filter(stream: Iterator[str]) -> Iterator[str]:
        for line in stream:
            if regex.search(line):
                yield line
    return _filter

def cut(field: int, delimiter: str = "|") -> Callable[[Iterator[str]], Iterator[str]]:
    """Extract field (0-indexed) from delimited stream"""
    def _transform(stream: Iterator[str]) -> Iterator[str]:
        for line in stream:
            parts = line.split(delimiter)
            if field < len(parts):
                yield parts[field]
    return _transform

def sort_stream() -> Callable[[Iterator[str]], Iterator[str]]:
    """Sort lines (materializes stream)"""
    def _sort(stream: Iterator[str]) -> Iterator[str]:
        yield from sorted(stream)
    return _sort

def uniq() -> Callable[[Iterator[str]], Iterator[str]]:
    """Remove consecutive duplicate lines"""
    def _uniq(stream: Iterator[str]) -> Iterator[str]:
        prev = None
        for line in stream:
            if line != prev:
                yield line
                prev = line
    return _uniq

def pipe(stream: Iterator[str], *transforms: Callable) -> Iterator[str]:
    """Compose stream transformations left-to-right"""
    result = stream
    for transform in transforms:
        result = transform(result)
    return result

if __name__ == "__main__":
    # Example: list active modules, extract names, sort
    result = pipe(
        stream_modules(),
        grep("active"),
        cut(0),
        sort_stream()
    )
    for line in result:
        print(line)