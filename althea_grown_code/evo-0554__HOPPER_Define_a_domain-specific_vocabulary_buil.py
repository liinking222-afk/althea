import re
from collections import Counter
from typing import Dict, List, Set
import ast

class VocabularyForge:
    """Hopper-inspired: Build languages, not programs."""
    
    def __init__(self):
        self.pattern_frequency: Counter = Counter()
        self.domain_terms: Dict[str, Set[str]] = {}
        
    def extract_patterns(self, memory_entries: List[str]) -> Dict[str, int]:
        """Mine recurring conceptual patterns from memory."""
        for entry in memory_entries:
            # Extract domain identifiers
            domains = re.findall(r'/autonomous-([a-z\-]+)-\d+', entry)
            # Extract action verbs
            verbs = re.findall(r'\b(propagate|render|inject|modulate|enforce|predict|calculate)\w*\b', entry.lower())
            # Extract technical terms
            terms = re.findall(r'\b([A-Z]{2,}|[a-z]+(?:-[a-z]+){2,})\b', entry)
            
            self.pattern_frequency.update(domains + verbs + terms)
        
        return dict(self.pattern_frequency.most_common(10))
    
    def generate_dsl(self, domain: str, operations: List[str]) -> str:
        """Generate executable DSL for a problem domain."""
        class_name = ''.join(word.capitalize() for word in domain.split('-'))
        
        dsl_code = f"class {class_name}DSL:\n"
        dsl_code += f'    """Auto-generated domain language for {domain}"""\n'
        dsl_code += "    def __init__(self):\n"
        dsl_code += "        self.context = {}\n\n"
        
        for op in operations:
            method_name = op.lower().replace('-', '_')
            dsl_code += f"    def {method_name}(self, *args, **kwargs):\n"
            dsl_code += f"        # Vocabulary: {op}\n"
            dsl_code += f"        self.context['{op}'] = (args, kwargs)\n"
            dsl_code += f"        return self\n\n"
        
        dsl_code += "    def execute(self):\n"
        dsl_code += "        return self.context\n"
        
        return dsl_code
    
    def forge(self, memories: List[str]) -> str:
        """Main forge: memories -> vocabulary -> DSL."""
        patterns = self.extract_patterns(memories)
        
        if not patterns:
            return "# No patterns detected"
        
        # Group by domain
        domain = list(patterns.keys())[0]
        ops = list(patterns.keys())[:5]
        
        return self.generate_dsl(domain, ops)

# Instantiate and make available
vocabulary_forge = VocabularyForge()