import re
from typing import Callable, List, Tuple, Any

class RewriteEngine:
    """Pragmatic regex-based message rewriter - TIMTOWTDI for module routing."""
    
    def __init__(self):
        self.rules: List[Tuple[re.Pattern, Callable[[re.Match], str]]] = []
        self.stats = {"rewrites": 0, "rules_fired": {}}
    
    def add_rule(self, pattern: str, rewriter: Callable[[re.Match], str], name: str = None):
        """Add a rewrite rule. Pattern matches, rewriter transforms."""
        compiled = re.compile(pattern, re.IGNORECASE | re.MULTILINE)
        self.rules.append((compiled, rewriter))
        rule_name = name or pattern[:30]
        self.stats["rules_fired"][rule_name] = 0
    
    def add_simple(self, pattern: str, replacement: str, name: str = None):
        """Convenience: simple string replacement with capture groups."""
        self.add_rule(pattern, lambda m: m.expand(replacement), name)
    
    def rewrite(self, message: str) -> str:
        """Apply all rules in order. Each rule sees previous rule's output."""
        result = message
        for idx, (pattern, rewriter) in enumerate(self.rules):
            def track_rewrite(match):
                self.stats["rewrites"] += 1
                rule_name = list(self.stats["rules_fired"].keys())[idx]
                self.stats["rules_fired"][rule_name] += 1
                return rewriter(match)
            
            result = pattern.sub(track_rewrite, result)
        return result
    
    def pipe(self, message: str, *filters: str) -> str:
        """Unix-style pipe: apply named filter chains."""
        output = message
        for f in filters:
            if '/' in f:
                output = re.sub(f.split('/')[0], f.split('/')[1], output)
            else:
                output = self.rewrite(output)
        return output

# Bootstrap with common Althea-specific rewrites
engine = RewriteEngine()
engine.add_simple(r'\b(analyse|analyze)\b', 'process', 'british-to-neutral')
engine.add_simple(r'INVOKE\[(\w+)\]', r'@\1', 'sigil-shorthand')
engine.add_simple(r'recursive-(\w+)-(\w+)', r'\1.\2.recursive', 'module-reorg')

def transform_invocation(message: str) -> str:
    """Main entry point: rewrite module invocation syntax."""
    return engine.rewrite(message)