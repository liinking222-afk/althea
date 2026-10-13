#!/usr/bin/env env python3
import re
from collections import Counter

def extract_verb_object(text):
    """Return (verb, object) tuple representing the ONE thing."""
    verbs = r'\b(build|extract|define|erode|reconstruct|bind|decay|validate|excavate|generate|prove|influence|detect|express|check|wipe)\w*\b'
    match = re.search(verbs, text.lower())
    if not match:
        return None, None
    verb = match.group()
    remainder = text[match.end():].strip()
    obj = remainder.split()[0:3] if remainder else []
    return verb, ' '.join(obj)

def analyze_memory_clarity(memory_lines):
    """Score each memory by Kernighan clarity: does it do ONE thing?"""
    results = []
    for line in memory_lines:
        if not line.strip() or line.startswith('[SYSTEM-MAP]'):
            continue
        verbs_found = re.findall(
            r'\b(build|extract|define|erode|reconstruct|bind|decay|validate|excavate|generate|prove|influence|detect|express|check|wipe)\w*\b',
            line.lower()
        )
        verb, obj = extract_verb_object(line)
        clarity_score = 1.0 / max(len(verbs_found), 1)
        results.append({
            'text': line[:80],
            'verb_count': len(verbs_found),
            'primary_verb': verb,
            'clarity': clarity_score
        })
    return results

def report(results):
    """Print clarity analysis with actionable violations."""
    print("CLARITY AUDIT")
    print("-" * 60)
    for r in sorted(results, key=lambda x: x['clarity']):
        indicator = "✓" if r['verb_count'] == 1 else "✗"
        print(f"{indicator} [{r['verb_count']} verbs] {r['clarity']:.2f} | {r['text']}")
    
    avg_clarity = sum(r['clarity'] for r in results) / len(results)
    print(f"\nAVG CLARITY: {avg_clarity:.2f} (1.0 = perfect)")

if __name__ == '__main__':
    import sys
    memory_lines = sys.stdin.readlines() if not sys.stdin.isatty() else []
    results = analyze_memory_clarity(memory_lines)
    report(results)