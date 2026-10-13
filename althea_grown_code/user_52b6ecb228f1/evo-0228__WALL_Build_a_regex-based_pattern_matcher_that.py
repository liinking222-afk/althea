#!/usr/bin/env python3
import re
from collections import Counter
from typing import List, Dict

class StyleCoherenceDetector:
    """Detects tonal/stylistic shifts within text using regex patterns."""
    
    STYLE_PATTERNS = {
        'technical': [
            r'\b(function|module|class|implementation|algorithm|runtime)\b',
            r'\b(optimize|refactor|compile|debug|execute)\b',
            r'[a-z_]+\(\)',  # function calls
        ],
        'poetic': [
            r'\b(dance|sing|weave|bloom|whisper|echo)\b',
            r'\b(garden|ocean|river|storm|light|shadow)\b',
            r'[.!?]\s+[A-Z][a-z]+\s+(like|as)\s+',  # similes
        ],
        'academic': [
            r'\b(hypothesis|theorem|axiom|paradigm|framework)\b',
            r'\b(thus|therefore|consequently|furthermore|moreover)\b',
            r'\bcf\.|i\.e\.|e\.g\.',
        ],
        'imperative': [
            r'^[A-Z][a-z]+\s+the\s+',  # Command-style starts
            r'\bYou (must|should|need to|will)\b',
            r'\b(Do not|Never|Always|Ensure)\b',
        ],
        'explanatory': [
            r'\bThis (means|indicates|suggests|implies)\b',
            r'\bIn other words\b',
            r'\b(because|since|due to)\b',
        ]
    }
    
    def scan(self, text: str) -> Dict:
        """Returns style distribution and shift points."""
        sentences = re.split(r'[.!?]+\s+', text)
        sentence_styles = []
        
        for sent in sentences:
            if len(sent.strip()) < 10:
                continue
            scores = {}
            for style, patterns in self.STYLE_PATTERNS.items():
                score = sum(len(re.findall(p, sent, re.IGNORECASE)) 
                           for p in patterns)
                scores[style] = score
            
            dominant = max(scores, key=scores.get) if max(scores.values()) > 0 else 'neutral'
            sentence_styles.append(dominant)
        
        shifts = sum(1 for i in range(1, len(sentence_styles)) 
                    if sentence_styles[i] != sentence_styles[i-1])
        
        distribution = Counter(sentence_styles)
        coherence_ratio = max(distribution.values()) / len(sentence_styles) if sentence_styles else 1.0
        
        return {
            'styles': dict(distribution),
            'shifts': shifts,
            'coherence': coherence_ratio,
            'mixed': len(distribution) > 2 and coherence_ratio < 0.6
        }

if __name__ == '__main__':
    detector = StyleCoherenceDetector()
    sample = "Optimize the function. The river flows through consciousness. Therefore, execute the module."
    result = detector.scan(sample)
    print(f"Mixed: {result['mixed']}, Shifts: {result['shifts']}, Styles: {result['styles']}")