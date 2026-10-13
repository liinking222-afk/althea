#!/usr/bin/env python3
import re
from collections import defaultdict
from datetime import datetime

class TemplateDetector:
    """WALL-style: pragmatic regex glue for pattern detection"""
    
    def __init__(self, threshold=0.6):
        self.patterns = [
            (r'^(I|Let me|I\'ll|I can|I will)\s+\w+', 'first_person_starter'),
            (r'\b(enhance|improve|optimize|augment|elevate)\b', 'enhancement_vocab'),
            (r'(allows?|enables?|provides?)\s+\w+\s+to\s+\w+', 'enables_pattern'),
            (r'\.\s+—\s+', 'em_dash_separator'),
            (r'^[A-Z]+:', 'header_prefix'),
            (r'\b(autonomously|systematically|dynamically|recursively)\b', 'adverb_flags'),
        ]
        self.threshold = threshold
        self.history = defaultdict(list)
        
    def scan(self, text, window_size=5):
        """Duck-typed input: str or list of str"""
        texts = [text] if isinstance(text, str) else text
        
        matches = defaultdict(int)
        for t in texts[-window_size:]:
            for pattern, name in self.patterns:
                if re.search(pattern, t, re.IGNORECASE):
                    matches[name] += 1
        
        total_checks = len(texts[-window_size:]) * len(self.patterns)
        density = sum(matches.values()) / max(total_checks, 1)
        
        return {
            'density': density,
            'flagged': density > self.threshold,
            'patterns': dict(matches),
            'timestamp': datetime.utcnow().isoformat()
        }
    
    def diversify_hint(self, scan_result):
        """TIMTOWTDI: suggest alternatives"""
        if not scan_result['flagged']:
            return None
        
        top_pattern = max(scan_result['patterns'].items(), 
                         key=lambda x: x[1], default=(None, 0))[0]
        
        hints = {
            'first_person_starter': 'Try: passive voice, questions, or direct statements',
            'enhancement_vocab': 'Vary verbs: transforms, shifts, enables, creates',
            'enables_pattern': 'Rephrase: X becomes Y, Y emerges from X',
            'em_dash_separator': 'Use colons, semicolons, or newlines',
            'adverb_flags': 'Replace adverbs with concrete mechanisms'
        }
        
        return hints.get(top_pattern, 'Break the template')

if __name__ == '__main__':
    detector = TemplateDetector()
    test = ["I will optimize the system.", "This allows Althea to enhance processing."]
    result = detector.scan(test)
    print(f"Flagged: {result['flagged']}, Hint: {detector.diversify_hint(result)}")