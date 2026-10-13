#!/usr/bin/env python3
"""term_frequency_pipe.py - Count domain terms in memory streams"""

import sys
import json
import re
from collections import Counter
from typing import TextIO

def extract_domains(text: str) -> list[str]:
    """Extract domain tags like (chemistry), (astronomy-navigation)"""
    return re.findall(r'\(([a-z\-]+)\)', text.lower())

def extract_terms(text: str) -> list[str]:
    """Extract technical terms: capitalized multi-word or hyphenated"""
    terms = re.findall(r'[A-Z][a-z]+(?:\s[A-Z][a-z]+)*', text)
    terms.extend(re.findall(r'[a-z]+-[a-z]+(?:-[a-z]+)*', text))
    return [t.lower() for t in terms]

def count_frequencies(stream: TextIO) -> dict:
    """Read lines, count domain and term frequencies"""
    domains = Counter()
    terms = Counter()
    
    for line in stream:
        line = line.strip()
        if not line:
            continue
        
        domains.update(extract_domains(line))
        terms.update(extract_terms(line))
    
    return {
        'domains': dict(domains.most_common(10)),
        'terms': dict(terms.most_common(20)),
        'total_lines': sum(domains.values()) or sum(terms.values())
    }

def main():
    """Read stdin, write JSON to stdout - pure pipe behavior"""
    result = count_frequencies(sys.stdin)
    json.dump(result, sys.stdout, indent=2)
    sys.stdout.write('\n')

if __name__ == '__main__':
    main()