import re
from dataclasses import dataclass
from typing import Callable, List, Tuple

@dataclass
class Transform:
    name: str
    input_type: str
    output_type: str
    pattern: str

def compose(*transforms: Transform) -> Callable[[str], Tuple[bool, List[str]]]:
    """Compose transforms as algebraic functions, verify type alignment."""
    def verify_composition():
        violations = []
        for i in range(len(transforms) - 1):
            if transforms[i].output_type != transforms[i + 1].input_type:
                violations.append(f"Type mismatch: {transforms[i].name} → {transforms[i+1].name}")
        return violations
    
    comp_violations = verify_composition()
    
    def composed(text: str) -> Tuple[bool, List[str]]:
        violations = comp_violations.copy()
        
        # Check for impure elements (prose, apologies, explanations)
        impurity_patterns = [
            (r'\b(sorry|apologize|let me explain|note that|importantly)\b', 'apologetic_prose'),
            (r'^[^`]*?(?:Here\'s|This is|I\'ve|I have)', 'explanatory_preamble'),
            (r'