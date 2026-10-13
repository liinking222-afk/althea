import re
from collections import defaultdict
from pathlib import Path

class ModuleDependencyAnalyzer:
    """Woz-inspired: count every chip. Map actual usage, not declared imports."""
    
    def __init__(self):
        self.call_graph = defaultdict(set)
        self.import_graph = defaultdict(set)
        self.module_sizes = {}
        
    def analyze_file(self, filepath: str, content: str):
        """Parse actual function calls vs declared imports."""
        module_name = Path(filepath).stem
        
        # Count actual LOC (not comments/blanks)
        loc = len([l for l in content.split('\n') 
                   if l.strip() and not l.strip().startswith('#')])
        self.module_sizes[module_name] = loc
        
        # Extract imports
        for match in re.finditer(r'from\s+(\w+)\s+import|import\s+(\w+)', content):
            imported = match.group(1) or match.group(2)
            self.import_graph[module_name].add(imported)
        
        # Extract actual calls (module.function or Class invocations)
        for match in re.finditer(r'(\w+)\.[a-z_]\w*\(|(\w+)\([^)]*\)', content):
            called = match.group(1) or match.group(2)
            if called and called[0].isupper():  # Class instantiation
                self.call_graph[module_name].add(called)
            elif called:
                self.call_graph[module_name].add(called)
    
    def find_unused_imports(self):
        """Woz principle: every chip must earn its place."""
        waste = {}
        for module, imports in self.import_graph.items():
            called = self.call_graph.get(module, set())
            unused = imports - called
            if unused:
                waste[module] = unused
        return waste
    
    def find_kernel(self):
        """Find minimal set of modules that support all others."""
        all_called = set()
        for calls in self.call_graph.values():
            all_called.update(calls)
        
        all_modules = set(self.module_sizes.keys())
        never_called = all_modules - all_called
        
        return {
            'kernel': all_called,
            'leaf_modules': never_called,
            'total_kernel_loc': sum(self.module_sizes.get(m, 0) for m in all_called)
        }
    
    def efficiency_report(self):
        """Hardware-minded: what's the utilization rate?"""
        waste = self.find_unused_imports()
        kernel = self.find_kernel()
        total_loc = sum(self.module_sizes.values())
        
        return {
            'total_modules': len(self.module_sizes),
            'total_loc': total_loc,
            'kernel_modules': len(kernel['kernel']),
            'kernel_loc': kernel['total_kernel_loc'],
            'efficiency': kernel['total_kernel_loc'] / total_loc if total_loc else 0,
            'unused_imports': waste,
            'candidate_removals': kernel['leaf_modules']
        }

# Runtime interface
def analyze_codebase(file_dict):
    analyzer = ModuleDependencyAnalyzer()
    for path, content in file_dict.items():
        analyzer.analyze_file(path, content)
    return analyzer.efficiency_report()