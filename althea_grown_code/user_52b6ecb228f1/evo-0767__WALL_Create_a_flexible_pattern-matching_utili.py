#!/usr/bin/env python3
import re
from collections import defaultdict
from typing import List, Dict, Tuple

class PatternScout:
    """WALL archetype: pragmatic detection, multiple strategies, optimize for writer & reader."""
    
    def __init__(self):
        self.signal_counts = defaultdict(int)
        self.keyword_clusters = defaultdict(list)
        
    def scan(self, text: str) -> List[Tuple[str, float, str]]:
        """Returns (pattern_name, confidence, evidence) tuples."""
        findings = []
        
        # Strategy 1: Domain keyword clustering (duck-typing approach)
        domains = {
            'crypto': r'\b(bitcoin|ethereum|blockchain|wallet|crypto|defi|nft)\b',
            'weather': r'\b(forecast|temperature|weather|climate|rain|sunny)\b',
            'code-analysis': r'\b(refactor|lint|complexity|analyze|ast|parse)\b',
            'translation': r'\b(translate|language|español|français|deutsch|中文)\b',
            'scheduling': r'\b(calendar|schedule|meeting|appointment|reminder)\b',
        }
        
        for domain, pattern in domains.items():
            matches = re.findall(pattern, text.lower())
            if len(matches) >= 2:
                findings.append((domain, len(matches) / 10.0, f"keywords:{matches[:3]}"))
        
        # Strategy 2: Question clustering (TIMTOWTDI - detect implicit need)
        question_patterns = [
            (r'how (?:do i|can i|to) (\w+)', 'action'),
            (r'what is (?:the |a )?(\w+)', 'definition'),
            (r'when (?:is|was|will) (\w+)', 'temporal'),
        ]
        
        for qpattern, qtype in question_patterns:
            if re.search(qpattern, text.lower()):
                self.signal_counts[qtype] += 1
                if self.signal_counts[qtype] >= 2:
                    findings.append((f"{qtype}-inquiry", 0.6, f"repeated:{self.signal_counts[qtype]}x"))
        
        # Strategy 3: API-shaped requests (pragmatic glue detection)
        if re.search(r'\b(get|fetch|retrieve|query|lookup|find)\b.*\b(data|info|information)\b', text.lower()):
            findings.append(('data-retrieval', 0.7, 'api-intent-detected'))
        
        return sorted(findings, key=lambda x: x[1], reverse=True)
    
    def suggest_module(self, pattern: str) -> str:
        """Map detected pattern to module name (optimizing for reader clarity)."""
        mapping = {
            'crypto': '/autonomous-crypto-price',
            'weather': '/autonomous-weather-forecast',
            'code-analysis': '/autonomous-code-quality',
            'translation': '/autonomous-translate',
            'scheduling': '/autonomous-calendar',
            'temporal-inquiry': '/autonomous-temporal-orient',
            'data-retrieval': '/autonomous-data-fetch',
        }
        return mapping.get(pattern, f'/autonomous-{pattern}')

if __name__ == '__main__':
    scout = PatternScout()
    test = "What's the bitcoin price? I need to check ethereum too."
    print(scout.scan(test))