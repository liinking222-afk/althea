import re
from pathlib import Path
from collections import defaultdict
from typing import Dict, Set, List

def extract_dependencies(source_code: str, module_name: str) -> Set[str]:
    """Extract imported module names from source using minimal regex patterns."""
    deps = set()
    
    # Python imports: import X, from X import Y
    for match in re.finditer(r'^\s*(?:from\s+(\S+)|import\s+(\S+))', source_code, re.MULTILINE):
        imported = match.group(1) or match.group(2)
        if imported and not imported.startswith('.'):
            deps.add(imported.split('.')[0])
    
    # Cross-module calls: /module-name or #module-name patterns
    for match in re.finditer(r'[/#]([a-z\-]+(?:\-[a-z]+)*)', source_code):
        if match.group(1) != module_name:
            deps.add(match.group(1))
    
    return deps

def scan_modules(base_path: Path = Path('.')) -> Dict[str, Set[str]]:
    """Scan all .py files and build dependency graph with minimal memory."""
    graph = defaultdict(set)
    
    for py_file in base_path.rglob('*.py'):
        if py_file.name.startswith('_'):
            continue
        
        module_name = py_file.stem
        try:
            source = py_file.read_text(encoding='utf-8')
            graph[module_name] = extract_dependencies(source, module_name)
        except Exception:
            continue
    
    return dict(graph)

def find_coupling_clusters(graph: Dict[str, Set[str]], threshold: int = 2) -> List[Set[str]]:
    """Identify tightly coupled module clusters."""
    clusters = []
    visited = set()
    
    for module in graph:
        if module in visited:
            continue
        
        cluster = {module}
        deps = graph[module]
        
        # Find bidirectional dependencies
        for dep in deps:
            if dep in graph and module in graph[dep]:
                cluster.add(dep)
        
        if len(cluster) >= threshold:
            clusters.append(cluster)
            visited.update(cluster)
    
    return clusters

def report_waste(graph: Dict[str, Set[str]]) -> Dict[str, int]:
    """Identify modules with high fan-out (potential inefficiency)."""
    return {mod: len(deps) for mod, deps in graph.items() if len(deps) > 5}

# Runtime introspection interface
def analyze(path: str = '.') -> dict:
    graph = scan_modules(Path(path))
    return {
        'graph': {k: list(v) for k, v in graph.items()},
        'clusters': [list(c) for c in find_coupling_clusters(graph)],
        'high_fanout': report_waste(graph)
    }