#!/usr/bin/env python3
import sys
import re
from collections import Counter

def extract_nouns(text):
    """Extract candidate nouns: capitalized words and common noun patterns."""
    words = re.findall(r'\b[A-Z][a-z]+\b|\b[a-z]{4,}\b', text)
    return [w.lower() for w in words if len(w) > 3]

def most_frequent_noun(text):
    """Return the single most frequent noun and its count."""
    nouns = extract_nouns(text)
    if not nouns:
        return None, 0
    counter = Counter(nouns)
    return counter.most_common(1)[0]

def main():
    text = sys.stdin.read()
    noun, count = most_frequent_noun(text)
    if noun:
        print(f"{noun}:{count}")
    else:
        print("none:0")

if __name__ == "__main__":
    main()