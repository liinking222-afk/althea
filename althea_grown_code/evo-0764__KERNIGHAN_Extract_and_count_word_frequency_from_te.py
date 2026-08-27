#!/usr/bin/env python3
"""
wordfreq - Count word frequency in text, output sorted by frequency.
Usage: cat file.txt | wordfreq [--top N]
"""
import sys
import re
from collections import Counter

def extract_words(text):
    """Return lowercase words, excluding punctuation."""
    return re.findall(r'\b[a-z]+\b', text.lower())

def count_frequencies(words):
    """Return word frequency counter."""
    return Counter(words)

def format_output(counter, limit=None):
    """Yield frequency lines: count word."""
    items = counter.most_common(limit)
    for word, count in items:
        yield f"{count}\t{word}"

def main():
    limit = None
    if len(sys.argv) > 1 and sys.argv[1] == '--top':
        limit = int(sys.argv[2])
    
    text = sys.stdin.read()
    words = extract_words(text)
    frequencies = count_frequencies(words)
    
    for line in format_output(frequencies, limit):
        print(line)

if __name__ == '__main__':
    main()