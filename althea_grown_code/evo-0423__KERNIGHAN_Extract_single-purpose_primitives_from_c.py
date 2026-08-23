#!/usr/bin/env python3
import re
from pathlib import Path
from collections import Counter

def tokenize_module_name(name):
    """Split module name into semantic atoms."""
    clean = re.sub(r'^(autonomous-|/)', '', name)
    clean = re.sub(r'-[a-f0-9]{4,}$', '', clean)
    tokens = re.split(r'[-_/]', clean)
    return [t.lower() for t in tokens if len(t) > 2]

def read_module_names(memory_file):
    """Extract module names from memory log."""
    if not Path(memory_file).exists():
        return []
    with open(memory_file) as f:
        names = []
        for line in f:
            match = re.search(r'\[(GROWTH|EVO|AUTOSYNTH)\s+([^\]]+)\]', line)
            if match:
                names.append(match.group(2).strip())
        return names

def extract_primitives(names, min_frequency=2):
    """Find recurring semantic atoms."""
    counter = Counter()
    for name in names:
        tokens = tokenize_module_name(name)
        counter.update(tokens)
    return {word: count for word, count in counter.items() if count >= min_frequency}

def generate_vocabulary(primitives):
    """Create sorted vocabulary list."""
    sorted_prims = sorted(primitives.items(), key=lambda x: (-x[1], x[0]))
    return [word for word, _ in sorted_prims]

def main():
    names = read_module_names('memory.log')
    if not names:
        names = []
    primitives = extract_primitives(names)
    vocab = generate_vocabulary(primitives)
    
    with open('semantic_primitives.txt', 'w') as f:
        for word in vocab:
            f.write(f"{word}\n")
    
    print(f"Extracted {len(vocab)} primitives")

if __name__ == '__main__':
    main()