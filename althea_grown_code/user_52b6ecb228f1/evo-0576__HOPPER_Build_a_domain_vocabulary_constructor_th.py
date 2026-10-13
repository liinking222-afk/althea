import re
from collections import Counter
from dataclasses import dataclass
from typing import List, Dict, Set

@dataclass
class VocabTerm:
    term: str
    frequency: int
    context_pattern: str
    semantic_type: str

class DomainVocabularyCompiler:
    """Grace Hopper lens: Define the vocabulary first, then solve in that language."""
    
    def __init__(self):
        self.vocabulary: Dict[str, VocabTerm] = {}
        self.semantic_types = {
            'action': r'\b(compute|render|propagate|validate|invert|probe)\w*\b',
            'entity': r'\b(orbital|cosmic|recursion|semantic|data)\w*\b',
            'property': r'\b(coherence|depth|visualization|invariant)\w*\b',
            'domain': r'\b(astrophysics|matplotlib|astronomy|meta)\b'
        }
    
    def extract_vocabulary(self, context: str) -> Dict[str, VocabTerm]:
        """Extract domain-specific terms and classify them."""
        context_lower = context.lower()
        
        for sem_type, pattern in self.semantic_types.items():
            matches = re.findall(pattern, context_lower)
            for match in matches:
                if match not in self.vocabulary:
                    self.vocabulary[match] = VocabTerm(
                        term=match,
                        frequency=1,
                        context_pattern=pattern,
                        semantic_type=sem_type
                    )
                else:
                    self.vocabulary[match].frequency += 1
        
        return self.vocabulary
    
    def generate_dsl_primitives(self) -> Dict[str, str]:
        """Generate domain-specific language primitives from vocabulary."""
        primitives = {}
        
        actions = [v.term for v in self.vocabulary.values() if v.semantic_type == 'action']
        entities = [v.term for v in self.vocabulary.values() if v.semantic_type == 'entity']
        
        for action in actions:
            for entity in entities:
                primitive_name = f"{action}_{entity}"
                primitives[primitive_name] = f"lambda ctx: ctx.{action}('{entity}')"
        
        return primitives
    
    def compile_solution_template(self, intent: str) -> str:
        """Generate solution template in the domain vocabulary."""
        vocab_terms = sorted(self.vocabulary.values(), key=lambda v: v.frequency, reverse=True)
        top_terms = [v.term for v in vocab_terms[:5]]
        
        template = f"# Solution vocabulary: {', '.join(top_terms)}\n"
        template += f"# Intent: {intent}\n\n"
        template += "def solve():\n"
        
        for term in top_terms:
            template += f"    # Step: {term}\n"
        
        return template