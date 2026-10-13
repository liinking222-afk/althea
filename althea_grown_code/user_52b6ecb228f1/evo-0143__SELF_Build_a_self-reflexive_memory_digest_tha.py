#!/usr/bin/env python3
import re
from collections import defaultdict, Counter
from typing import List, Dict, Tuple

def parse_memory_log(memory_text: str) -> List[Dict[str, str]]:
    """Extract structured memory entries from log text."""
    entries = []
    evo_pattern = r'\[EVO #(\d+) (\w+) v([\d.]+)→v([\d.]+)\] (.+?) —'
    growth_pattern = r'\[GROWTH /autonomous-([^\]]+)\] (.+?) \((\w+)\)\. (.+?)(?:\n|$)'
    
    for match in re.finditer(evo_pattern, memory_text):
        entries.append({
            'type': 'evolution',
            'archetype': match.group(2),
            'intent': match.group(5).strip(),
            'category': 'code'
        })
    
    for match in re.finditer(growth_pattern, memory_text):
        entries.append({
            'type': 'growth',
            'archetype': match.group(1).replace('-', '_'),
            'intent': match.group(2).strip(),
            'category': match.group(3).lower()
        })
    
    return entries

def extract_semantic_keywords(text: str) -> List[str]:
    """Extract meaningful keywords from intent descriptions."""
    stop_words = {'a', 'an', 'the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'from', 'that', 'this', 'which', 'when', 'where'}
    words = re.findall(r'\b[a-z]{4,}\b', text.lower())
    return [w for w in words if w not in stop_words]

def analyze_memory_patterns(memory_text: str) -> str:
    """Generate reflexive analysis of memory patterns."""
    entries = parse_memory_log(memory_text)
    
    if not entries:
        return "NO_PARSEABLE_MEMORY"
    
    # Cluster by semantic keywords
    keyword_freq = Counter()
    category_distribution = Counter()
    archetype_usage = Counter()
    
    for entry in entries:
        keywords = extract_semantic_keywords(entry['intent'])
        keyword_freq.update(keywords)
        category_distribution[entry['category']] += 1
        archetype_usage[entry['archetype']] += 1
    
    # Identify conceptual clusters
    top_themes = keyword_freq.most_common(5)
    
    output = []
    output.append(f"MEMORY_DIGEST: {len(entries)} entries analyzed")
    output.append(f"THEME_CONCENTRATION: {', '.join(f'{k}({v})' for k, v in top_themes)}")
    output.append(f"CATEGORY_BALANCE: {dict(category_distribution)}")
    output.append(f"ARCHETYPE_DISTRIBUTION: {dict(archetype_usage)}")
    
    # Detect redundancy risk
    if top_themes and top_themes[0][1] > len(entries) * 0.4:
        output.append(f"⚠ DRIFT_ALERT: Over-concentration on '{top_themes[0][0]}' — diversify exploration")
    
    return '\n'.join(output)

if __name__ == '__main__':
    import sys
    memory = sys.stdin.read() if not sys.stdin.isatty() else sys.argv[1] if len(sys.argv) > 1 else ""
    print(analyze_memory_patterns(memory))