#!/usr/bin/env python3
import re
import sys
from typing import Callable, List, Tuple, Any, Dict

class PatternRouter:
    """Larry Wall style: regex-driven dispatch with maximal flexibility."""
    
    def __init__(self):
        self.routes: List[Tuple[re.Pattern, Callable, Dict[str, Any]]] = []
    
    def add(self, pattern: str, handler: Callable, flags: int = 0, **opts):
        """Register pattern->handler mapping. Capture groups become args."""
        compiled = re.compile(pattern, flags)
        self.routes.append((compiled, handler, opts))
        return self
    
    def route(self, input_text: str) -> Any:
        """Try patterns in order; first match wins (Perl-style)."""
        for pattern, handler, opts in self.routes:
            match = pattern.search(input_text)
            if match:
                groups = match.groups()
                groupdict = match.groupdict()
                
                # Duck-type the handler call
                try:
                    if groupdict:
                        return handler(**groupdict, **opts)
                    elif groups:
                        return handler(*groups, **opts)
                    else:
                        return handler(input_text, **opts)
                except TypeError:
                    return handler(match, **opts)
        return None
    
    def route_all(self, input_text: str) -> List[Any]:
        """Match ALL patterns (grep-style), return all results."""
        results = []
        for pattern, handler, opts in self.routes:
            for match in pattern.finditer(input_text):
                groups = match.groups()
                groupdict = match.groupdict()
                
                try:
                    if groupdict:
                        results.append(handler(**groupdict, **opts))
                    elif groups:
                        results.append(handler(*groups, **opts))
                    else:
                        results.append(handler(input_text, **opts))
                except TypeError:
                    results.append(handler(match, **opts))
        return results
    
    def pipe(self, input_text: str) -> str:
        """Chain transformations Unix-pipeline style."""
        result = input_text
        for pattern, handler, opts in self.routes:
            result = pattern.sub(lambda m: str(handler(m, **opts)), result)
        return result

if __name__ == "__main__":
    router = PatternRouter()
    router.add(r"(\w+)://(\S+)", lambda proto, path: f"Protocol:{proto} Path:{path}")
    router.add(r"\[(\w+)\]", lambda tag: tag.upper())
    
    for line in sys.stdin:
        print(router.route(line.strip()) or line.strip())