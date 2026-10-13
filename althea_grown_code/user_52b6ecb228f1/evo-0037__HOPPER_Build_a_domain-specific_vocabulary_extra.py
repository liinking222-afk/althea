#!/usr/bin/env python3
"""
Althea Vocabulary Crystallizer - Extract domain vocabularies from experience
"""

import re
from collections import defaultdict, Counter
from dataclasses import dataclass
from typing import List, Dict, Set

@dataclass
class ConceptSignature:
    symbol: str
    pattern: str
    frequency: int
    contexts: List[str]

class VocabularyCrystallizer:
    def __init__(self):
        self.concept_patterns = {
            r'\[([\w-]+)\]': 'TAG',
            r'(\w+)=[\w\-\.]+': 'BINDING',
            r'([\w-]+):': 'LABEL',
            r'NOTE: (.+?)\.': 'CONSTRAINT',
        }
        self.vocabulary: Dict[str, ConceptSignature] = {}
        
    def extract(self, memories: List[str]) -> Dict[str, ConceptSignature]:
        concept_freq = defaultdict(lambda: {'count': 0, 'contexts': []})
        
        for memory in memories:
            for pattern, ptype in self.concept_patterns.items():
                for match in re.finditer(pattern, memory):
                    concept = match.group(1) if match.lastindex else match.group(0)
                    key = f"{ptype}:{concept}"
                    concept_freq[key]['count'] += 1
                    concept_freq[key]['contexts'].append(memory[:60])
        
        # Crystallize high-frequency patterns into symbols
        for key, data in concept_freq.items():
            if data['count'] >= 2:  # Recurrence threshold
                ptype, concept = key.split(':', 1)
                symbol = self._symbolize(concept, ptype)
                self.vocabulary[symbol] = ConceptSignature(
                    symbol=symbol,
                    pattern=concept,
                    frequency=data['count'],
                    contexts=data['contexts'][:3]
                )
        
        return self.vocabulary
    
    def _symbolize(self, concept: str, ptype: str) -> str:
        prefix = {'TAG': '§', 'BINDING': '∂', 'LABEL': '∆', 'CONSTRAINT': '∇'}
        return f"{prefix.get(ptype, '•')}{concept.upper()[:8]}"
    
    def compile_grammar(self) -> str:
        lines = ["# CRYSTALLIZED VOCABULARY\n"]
        for sym, sig in sorted(self.vocabulary.items(), key=lambda x: -x[1].frequency):
            lines.append(f"{sym} := {sig.pattern} (×{sig.frequency})")
        return "\n".join(lines)

if __name__ == "__main__":
    vc = VocabularyCrystallizer()
    memories = [
        "[NETWORK-PROFILE] declared ssid='AlthEa-Test-Net' security=WPA2",
        "[SYSTEM-MAP] Althea subsystems and operator controls:",
        "NOTE: browsers cannot join wi-fi natively",
        "[REFLECTION node:NODE-0158 stream:pairing:usb]",
    ]
    vc.extract(memories)
    print(vc.compile_grammar())