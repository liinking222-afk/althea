import re
from dataclasses import dataclass
from typing import List, Dict, Set

@dataclass
class Token:
    type: str
    value: str
    context: str

class VocabularyExtractor:
    """Hopper-style vocabulary-first extraction from problem domains."""
    
    def __init__(self):
        self.vocabulary: Dict[str, Set[str]] = {
            "concepts": set(),
            "operations": set(),
            "constraints": set(),
            "relations": set()
        }
        self.patterns = {
            "concepts": r'\b([A-Z][a-z]+(?:[A-Z][a-z]+)*)\b',
            "operations": r'\b(verify|validate|capture|detect|amplify|map|eliminate|build|introduce)\b',
            "constraints": r'\b(invariant|boundary|overhead|zero-copy|formal|direct)\b',
            "relations": r'\b(across|over|at|into|from|without)\b'
        }
    
    def extract(self, text: str) -> List[Token]:
        """Extract domain vocabulary tokens from input text."""
        tokens = []
        for category, pattern in self.patterns.items():
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                value = match.group(1).lower()
                self.vocabulary[category].add(value)
                tokens.append(Token(
                    type=category,
                    value=value,
                    context=text[max(0, match.start()-20):min(len(text), match.end()+20)]
                ))
        return tokens
    
    def define_dsl(self) -> str:
        """Generate DSL grammar from extracted vocabulary."""
        dsl = "# Domain-Specific Language\n\n"
        for category, terms in self.vocabulary.items():
            if terms:
                dsl += f"{category.upper()} ::= {' | '.join(sorted(terms))}\n"
        return dsl
    
    def tokenize_solution(self, solution: str) -> List[Token]:
        """Parse solution using extracted vocabulary."""
        tokens = []
        for category in self.vocabulary:
            for term in self.vocabulary[category]:
                pattern = r'\b' + re.escape(term) + r'\b'
                for match in re.finditer(pattern, solution, re.IGNORECASE):
                    tokens.append(Token(category, term, solution[match.start():match.end()]))
        return sorted(tokens, key=lambda t: solution.find(t.value))

def hopper_compile(problem: str, solution: str) -> Dict:
    """Vocabulary-first compilation: extract language, then parse solution."""
    extractor = VocabularyExtractor()
    extractor.extract(problem)
    dsl = extractor.define_dsl()
    solution_tokens = extractor.tokenize_solution(solution)
    return {
        "vocabulary": extractor.vocabulary,
        "dsl": dsl,
        "solution_ast": solution_tokens
    }