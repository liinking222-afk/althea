#!/usr/bin/env python3
import re
from typing import Any, Callable, Iterator, Optional
from functools import reduce

class EventStream:
    """Pragmatic stream processor - there's more than one way to filter it."""
    
    def __init__(self, events: Iterator[dict]):
        self.events = events
    
    def grep(self, pattern: str, field: str = "type") -> "EventStream":
        """Regex filter - lean into what works."""
        regex = re.compile(pattern)
        def _filter():
            for event in self.events:
                if isinstance(event.get(field), str) and regex.search(event[field]):
                    yield event
        return EventStream(_filter())
    
    def map(self, fn: Callable[[dict], dict]) -> "EventStream":
        """Transform each event - duck typing heaven."""
        return EventStream(fn(e) for e in self.events)
    
    def where(self, **kwargs) -> "EventStream":
        """Filter by arbitrary fields - optimize for the writer."""
        def _filter():
            for event in self.events:
                if all(event.get(k) == v for k, v in kwargs.items()):
                    yield event
        return EventStream(_filter())
    
    def pluck(self, *fields) -> "EventStream":
        """Extract specific fields - readable intent."""
        def _filter():
            for event in self.events:
                yield {f: event.get(f) for f in fields if f in event}
        return EventStream(_filter())
    
    def tee(self, fn: Callable[[dict], None]) -> "EventStream":
        """Side-effect tap - pragmatic debugging."""
        def _filter():
            for event in self.events:
                fn(event)
                yield event
        return EventStream(_filter())
    
    def take(self, n: int) -> list:
        """Materialize n events - lazy until needed."""
        return [event for event, _ in zip(self.events, range(n))]
    
    def collect(self) -> list:
        """Materialize all events."""
        return list(self.events)
    
    def reduce(self, fn: Callable[[Any, dict], Any], initial: Any = None) -> Any:
        """Fold the stream - functional glue."""
        return reduce(fn, self.events, initial)

def stream(events: list) -> EventStream:
    """Entry point - clean API for the reader."""
    return EventStream(iter(events))