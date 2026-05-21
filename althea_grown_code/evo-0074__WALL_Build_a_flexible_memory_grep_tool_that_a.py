#!/usr/bin/env python3
import sys
import re
from difflib import SequenceMatcher

def fuzzy_match(pattern, text, threshold=0.6):
    return SequenceMatcher(None, pattern.lower(), text.lower()).ratio() >= threshold

def grep_memory(pattern, mode='regex', context=0, case_sensitive=False):
    memories = sys.stdin.read().strip().split('\n')
    flags = 0 if case_sensitive else re.IGNORECASE
    matches = []
    
    for i, line in enumerate(memories):
        hit = False
        if mode == 'regex':
            hit = re.search(pattern, line, flags)
        elif mode == 'literal':
            target = line if case_sensitive else line.lower()
            pat = pattern if case_sensitive else pattern.lower()
            hit = pat in target
        elif mode == 'fuzzy':
            hit = fuzzy_match(pattern, line)
        
        if hit:
            start = max(0, i - context)
            end = min(len(memories), i + context + 1)
            matches.append((i, start, end))
    
    # Merge overlapping contexts
    merged = []
    for idx, start, end in matches:
        if merged and start <= merged[-1][2]:
            merged[-1] = (merged[-1][0], merged[-1][1], max(end, merged[-1][2]))
        else:
            merged.append((idx, start, end))
    
    # Output with separators
    for match_idx, (hit_line, start, end) in enumerate(merged):
        if match_idx > 0:
            print("--")
        for i in range(start, end):
            prefix = ">" if i == hit_line else " "
            print(f"{prefix} {memories[i]}")

if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument('pattern')
    p.add_argument('-m', '--mode', choices=['regex', 'literal', 'fuzzy'], default='regex')
    p.add_argument('-C', '--context', type=int, default=0)
    p.add_argument('-c', '--case-sensitive', action='store_true')
    args = p.parse_args()
    grep_memory(args.pattern, args.mode, args.context, args.case_sensitive)