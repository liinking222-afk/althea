import re
from collections import Counter, defaultdict
from typing import Dict, List, Set, Tuple

class VocabularyCompiler:
    """HOPPER: Build languages from problem domains, not solutions."""
    
    def __init__(self):
        self.primitives: Dict[str, int] = Counter()
        self.operators: Dict[str, List[str]] = defaultdict(list)
        self.compositions: Set[Tuple[str, str]] = set()
    
    def extract_primitives(self, context: str) -> Dict[str, int]:
        """Identify atomic conceptual units from conversation."""
        pattern = r'\b([a-z]+(?:-[a-z]+)+)\b'
        matches = re.findall(pattern, context.lower())
        
        for match in matches:
            self.primitives[match] += 1
            parts = match.split('-')
            if len(parts) >= 2:
                self.operators[parts[-1]].append('-'.join(parts[:-1]))
                if len(parts) >= 3:
                    self.compositions.add((parts[0], '-'.join(parts[1:])))
        
        return dict(self.primitives.most_common(20))
    
    def synthesize_operator(self, operator_name: str) -> str:
        """Generate executable function from discovered operator pattern."""
        operands = self.operators.get(operator_name, [])
        if not operands:
            return f"def {operator_name}(x): return x"
        
        operand_set = ', '.join(f"'{op}'" for op in set(operands[:5]))
        return f"""def {operator_name}(concept, intensity=1.0):
    '''Operator: {operator_name} | Domain: [{operand_set}]'''
    return {{'op': '{operator_name}', 'input': concept, 'weight': intensity}}"""
    
    def compile_vocabulary(self, context: str) -> str:
        """Transform problem domain into executable mini-language."""
        self.extract_primitives(context)
        
        code = "# COMPILED VOCABULARY FROM DOMAIN\n\n"
        for op in sorted(self.operators.keys())[:10]:
            code += self.synthesize_operator(op) + "\n\n"
        
        code += f"# Primitives: {len(self.primitives)} | Operators: {len(self.operators)}\n"
        code += f"# Compositions: {len(self.compositions)}\n"
        
        return code

def invoke(context: str) -> str:
    compiler = VocabularyCompiler()
    return compiler.compile_vocabulary(context)