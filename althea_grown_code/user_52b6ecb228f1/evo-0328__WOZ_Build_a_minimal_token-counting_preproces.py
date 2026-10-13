import re
from typing import List, Tuple

class TokenEfficiencyFilter:
    """WOZ-style constraint optimizer: make every token count."""
    
    def __init__(self):
        self.patterns = [
            (r'\[GROWTH /autonomous-([^\]]+)\]', r'[G/\1]'),
            (r'\[EVO #(\d+) \w+ v([\d.]+)→([\d.]+)\]', r'[E#\1:\2→\3]'),
            (r'\[IMAGINED\] prompt\s*', r''),
            (r'\s*—\s*rationale:\s*\w+\s*$', r''),
            (r'(\w+)\s+\(testid:\s*[^)]+\)', r'\1'),
            (r'\s+—\s+', r' · '),
            (r'(?<=\w)\s{2,}(?=\w)', r' '),
        ]
        
        self.stopwords = {
            'which', 'that', 'allows', 'enables', 'provides', 
            'Althea', 'module', 'system'
        }
    
    def compress(self, text: str) -> str:
        """Squeeze maximum meaning from minimum tokens."""
        result = text
        
        for pattern, replacement in self.patterns:
            result = re.sub(pattern, replacement, result)
        
        lines = [line.strip() for line in result.split('\n') if line.strip()]
        result = '\n'.join(lines)
        
        return result
    
    def batch_compress(self, entries: List[str], target_ratio: float = 0.65) -> List[str]:
        """Compress batch until hitting target token ratio."""
        compressed = [self.compress(entry) for entry in entries]
        
        original_len = sum(len(e.split()) for e in entries)
        compressed_len = sum(len(e.split()) for e in compressed)
        
        if compressed_len / original_len > target_ratio:
            compressed = [self._aggressive_compress(e) for e in compressed]
        
        return compressed
    
    def _aggressive_compress(self, text: str) -> str:
        """Strip common stopwords when needed."""
        words = text.split()
        filtered = [w for w in words if w.lower() not in self.stopwords]
        return ' '.join(filtered) if filtered else text

if __name__ == '__main__':
    filter = TokenEfficiencyFilter()
    test = "[GROWTH /autonomous-resolution-collapse] Resolution Collapse (perception). Systematically degrade distinctions between previously separate concepts until they become indistinguishable. — rationale: To"
    print(filter.compress(test))