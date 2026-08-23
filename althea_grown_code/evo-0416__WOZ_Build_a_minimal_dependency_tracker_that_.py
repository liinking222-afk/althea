import re
from collections import defaultdict, deque
from typing import Dict, Set, List, Tuple

class DependencyGraph:
    def __init__(self):
        self.edges: Dict[str, Set[str]] = defaultdict(set)
        self.reverse: Dict[str, Set[str]] = defaultdict(set)
        
    def add(self, module: str, depends_on: str):
        self.edges[module].add(depends_on)
        self.reverse[depends_on].add(module)
    
    def parse_code(self, module_name: str, code: str):
        patterns = [
            r'^\s*import\s+([a-zA-Z0-9_\.]+)',
            r'^\s*from\s+([a-zA-Z0-9_\.]+)\s+import',
            r'require\(["\']([^"\']+)["\']\)',
            r'import\s+.*\s+from\s+["\']([^"\']+)["\']',
        ]
        for line in code.split('\n'):
            for pattern in patterns:
                match = re.search(pattern, line)
                if match:
                    dep = match.group(1).split('.')[0]
                    if dep != module_name:
                        self.add(module_name, dep)
    
    def cycles(self) -> List[List[str]]:
        visited, stack, result = set(), set(), []
        def dfs(node, path):
            if node in stack:
                cycle_start = path.index(node)
                result.append(path[cycle_start:])
                return
            if node in visited:
                return
            visited.add(node)
            stack.add(node)
            for dep in self.edges.get(node, []):
                dfs(dep, path + [dep])
            stack.remove(node)
        for node in self.edges:
            dfs(node, [node])
        return result
    
    def orphans(self) -> Set[str]:
        all_modules = set(self.edges.keys()) | set(self.reverse.keys())
        return {m for m in all_modules if not self.reverse[m] and m in self.edges}
    
    def report(self) -> str:
        lines = [f"MODULES: {len(self.edges)}"]
        cyc = self.cycles()
        if cyc:
            lines.append(f"CYCLES: {len(cyc)}")
            for c in cyc[:3]:
                lines.append(f"  {' → '.join(c + [c[0]])}")
        orp = self.orphans()
        if orp:
            lines.append(f"ORPHANS: {', '.join(sorted(orp))}")
        return '\n'.join(lines)

def analyze(modules: Dict[str, str]) -> str:
    graph = DependencyGraph()
    for name, code in modules.items():
        graph.parse_code(name, code)
    return graph.report()