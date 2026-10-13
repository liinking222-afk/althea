#!/usr/bin/env python3
import re
from typing import Dict, List, Optional, Any

class PolyglotModuleParser:
    """Parse module signatures flexibly - optimize for writer AND reader."""
    
    PATTERNS = {
        'intent': r'INTENT:\s*(.+?)(?=\n|$)',
        'language': r'LANGUAGE:\s*(\w+)',
        'verb': r'\b(build|extract|validate|parse|route|compose|cache|invert|plant|degrade)\b',
        'noun': r'\b(module|validator|router|cache|parser|pattern|seed|gradient)\b',
        'delta': r'DELTA:\s*(.+?)(?=\n|$)',
        'version': r'v?(\d+)\.(\d+)\.(\d+)',
    }
    
    def __init__(self):
        self.compiled = {k: re.compile(p, re.IGNORECASE) for k, p in self.PATTERNS.items()}
    
    def parse(self, text: str) -> Dict[str, Any]:
        """Duck-type the structure - there's more than one way to format it."""
        result = {}
        
        for key, pattern in self.compiled.items():
            match = pattern.search(text)
            if match:
                result[key] = match.groups() if len(match.groups()) > 1 else match.group(1)
        
        result['verbs'] = self.compiled['verb'].findall(text)
        result['nouns'] = self.compiled['noun'].findall(text)
        result['signature'] = self._compute_signature(result)
        
        return result
    
    def _compute_signature(self, parsed: Dict) -> str:
        """Pragmatic glue: combine verb+noun for fuzzy matching."""
        verbs = parsed.get('verbs', [])
        nouns = parsed.get('nouns', [])
        if verbs and nouns:
            return f"{verbs[0]}_{nouns[0]}"
        return "unknown_module"
    
    def can_compose(self, sig1: str, sig2: str) -> bool:
        """Check if two signatures can glue together (duck-typing style)."""
        parts1 = sig1.split('_')
        parts2 = sig2.split('_')
        # If output noun of sig1 matches input noun of sig2, composable
        return len(parts1) > 1 and len(parts2) > 1 and parts1[-1] == parts2[-1]
    
    def suggest_composition(self, modules: List[str]) -> List[tuple]:
        """Find all TIMTOWTDI composition paths."""
        parsed = [self.parse(m) for m in modules]
        sigs = [p.get('signature', '') for p in parsed]
        
        compositions = []
        for i, s1 in enumerate(sigs):
            for j, s2 in enumerate(sigs):
                if i != j and self.can_compose(s1, s2):
                    compositions.append((i, j, f"{s1}|>{s2}"))
        
        return compositions

parser = PolyglotModuleParser()