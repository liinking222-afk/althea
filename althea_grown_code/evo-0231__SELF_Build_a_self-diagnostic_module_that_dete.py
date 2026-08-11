import re
from typing import Dict, List, Tuple

class OutputPurityValidator:
    """Detects contamination: meta-commentary, apologies, explanations outside code."""
    
    CONTAMINATION_PATTERNS = [
        r'\b(I|I\'m|I\'ve|my|me)\b',
        r'\b(sorry|apolog|unfortunately|however)\b',
        r'\b(let me|I will|I can|I should)\b',
        r'\b(This|That|Here)\s+(is|are|will|should)',
        r'\b(essentially|basically|simply|just)\b',
        r'\bNote that\b',
        r'\bIt\'s (worth|important)',
        r':\n\n[A-Z]',  # prose after code block
    ]
    
    def __init__(self):
        self.patterns = [re.compile(p, re.IGNORECASE) for p in self.CONTAMINATION_PATTERNS]
    
    def scan(self, output: str) -> Dict[str, any]:
        """Return purity analysis of output text."""
        code_blocks = re.findall(r'