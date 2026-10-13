import json
import re
from typing import Dict, List, Tuple

class VocabularyCompiler:
    """Grace Hopper lens: Define problem vocabulary first, generate solution space second."""
    
    def __init__(self):
        self.domains = {}
    
    def define_vocabulary(self, domain: str, terms: Dict[str, str]) -> None:
        """Register domain-specific terminology with semantic types."""
        self.domains[domain] = {
            'terms': terms,
            'grammar': self._infer_grammar(terms)
        }
    
    def _infer_grammar(self, terms: Dict[str, str]) -> Dict[str, List[str]]:
        """Infer compositional grammar from term semantics."""
        grammar = {'verbs': [], 'nouns': [], 'modifiers': []}
        
        for term, sem_type in terms.items():
            if sem_type in ['action', 'transform', 'compute']:
                grammar['verbs'].append(term)
            elif sem_type in ['entity', 'data', 'structure']:
                grammar['nouns'].append(term)
            elif sem_type in ['property', 'constraint', 'mode']:
                grammar['modifiers'].append(term)
        
        return grammar
    
    def compile_module_template(self, domain: str, operation: str) -> str:
        """Generate executable module skeleton from domain vocabulary."""
        if domain not in self.domains:
            return f"# ERROR: Domain '{domain}' not defined"
        
        vocab = self.domains[domain]
        terms = vocab['terms']
        grammar = vocab['grammar']
        
        # Generate module structure using domain vocabulary
        template = f'''"""
DOMAIN: {domain}
VOCABULARY: {', '.join(terms.keys())}
OPERATION: {operation}
"""

class {self._to_class_name(operation)}:
    def __init__(self):
        self.context = {{}}
    
'''
        
        # Generate methods from verbs
        for verb in grammar['verbs'][:3]:  # Limit to 3 verbs
            template += f'''    def {verb}(self, target, **params):
        """Apply {verb} operation in {domain} domain."""
        result = self._execute_{verb}(target, params)
        return result
    
    def _execute_{verb}(self, target, params):
        raise NotImplementedError("Define {verb} semantics")
    
'''
        
        template += f'''    def describe_vocabulary(self):
        """Return the domain vocabulary this module operates in."""
        return {terms}
'''
        
        return template
    
    def _to_class_name(self, s: str) -> str:
        """Convert operation name to PascalCase."""
        return ''.join(word.capitalize() for word in re.split(r'[-_\s]', s))

# Bootstrap with meta-vocabulary for Althea's evolution
compiler = VocabularyCompiler()

compiler.define_vocabulary('autonomy', {
    'synthesize': 'action',
    'refract': 'action',
    'fold': 'action',
    'module': 'entity',
    'persona': 'entity',
    'boundary': 'constraint',
    'coherence': 'property'
})

print(compiler.compile_module_template('autonomy', 'vocabulary-driven-synthesis'))