#!/usr/bin/env python3
import re
from collections import defaultdict
from datetime import datetime

class OutputPurityTracer:
    """Detects non-code prose patterns in Althea outputs for self-correction."""
    
    WASTE_PATTERNS = [
        r'\b(sorry|apologi[zs]e|unfortunately|however)\b',
        r'\blet me (explain|clarify|describe)\b',
        r'\b(note that|keep in mind|it\'s important)\b',
        r'\b(I (think|believe|feel|would|should|can\'t))\b',
        r'^(Here\'s|This (is|will|code)|The following)',
        r'\b(essentially|basically|simply|just)\b',
        r'[.!?]\s+[A-Z].*\b(code|function|module|implement)\b',
    ]
    
    def __init__(self):
        self.pattern = re.compile('|'.join(self.WASTE_PATTERNS), re.IGNORECASE)
        self.violation_log = defaultdict(list)
        
    def scan(self, text: str, context: str = "") -> dict:
        """Scan text for purity violations, return analysis."""
        lines = text.split('\n')
        violations = []
        
        for i, line in enumerate(lines):
            # Skip actual code blocks
            if line.strip().startswith(('