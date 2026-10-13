#!/usr/bin/env python3
"""
Pattern Extractor - Pragmatic regex-based entity extraction
Optimized for both writing patterns and reading results
"""

import re
from typing import Any, Dict, List, Optional, Union

class PatternExtractor:
    """Duck-typed pattern matcher - if it quacks like data, extract it"""
    
    def __init__(self):
        self.patterns = {
            'chemical': r'\b([A-Z][a-z]?(?:\d+)?(?:[A-Z][a-z]?\d*)*)\b',
            'celestial': r'\b(planet|moon|asteroid|comet)\s+([A-Za-z0-9\s]+)',
            'number_with_unit': r'([\d,]+(?:\.\d+)?)\s*([a-zA-Z]+)',
            'date_like': r'\b(\d{1,4})[-/](\d{1,2})[-/](\d{1,4})\b',
            'command_verb': r'^\s*(show|create|get|find|lookup|compare|plot)\s+',
            'quoted': r'["\']([^"\']+)["\']',
            'range': r'(\d+(?:\.\d+)?)\s*(?:to|-|\.\.)\s*(\d+(?:\.\d+)?)',
        }
    
    def extract(self, text: str, pattern_name: Optional[str] = None) -> Union[List[str], Dict[str, List[str]]]:
        """TIMTOWTDI: extract by name or extract all"""
        if pattern_name:
            if pattern_name not in self.patterns:
                return []
            matches = re.findall(self.patterns[pattern_name], text, re.IGNORECASE)
            return [m if isinstance(m, str) else m[0] for m in matches]
        
        # Extract all patterns
        results = {}
        for name, pattern in self.patterns.items():
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                results[name] = [m if isinstance(m, str) else ' '.join(filter(None, m)) for m in matches]
        return results
    
    def add_pattern(self, name: str, regex: str) -> None:
        """Extensible - add patterns at runtime"""
        self.patterns[name] = regex
    
    def match_intent(self, text: str) -> Optional[str]:
        """Quick intent classification for routing"""
        text_lower = text.lower()
        if any(word in text_lower for word in ['element', 'molecule', 'chemical', 'compound']):
            return 'chemistry'
        if any(word in text_lower for word in ['planet', 'orbit', 'celestial', 'asteroid']):
            return 'astronomy'
        if any(word in text_lower for word in ['plot', 'chart', 'graph', 'visualize']):
            return 'visualization'
        return None

# Module interface
def extract_patterns(text: str, pattern: Optional[str] = None) -> Any:
    """Convenience function - because less typing matters"""
    extractor = PatternExtractor()
    return extractor.extract(text, pattern)

if __name__ == '__main__':
    # Self-test
    test = "Show me H2O and CO2 for planet Nibiru from 2020-01-15"
    ex = PatternExtractor()
    print(ex.extract(test))
    print(f"Intent: {ex.match_intent(test)}")