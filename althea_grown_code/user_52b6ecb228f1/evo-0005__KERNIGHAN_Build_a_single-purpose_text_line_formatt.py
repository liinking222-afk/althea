#!/usr/bin/env python3
import sys

def wrap_line(line, width=72):
    """Wrap a single line at word boundaries to specified width."""
    if len(line) <= width:
        return [line]
    
    words = line.split()
    wrapped = []
    current = []
    current_len = 0
    
    for word in words:
        word_len = len(word)
        space_len = 1 if current else 0
        
        if current_len + space_len + word_len <= width:
            current.append(word)
            current_len += space_len + word_len
        else:
            if current:
                wrapped.append(' '.join(current))
            current = [word]
            current_len = word_len
    
    if current:
        wrapped.append(' '.join(current))
    
    return wrapped

def main():
    for line in sys.stdin:
        line = line.rstrip('\n\r')
        if not line:
            print()
            continue
        
        for wrapped in wrap_line(line):
            print(wrapped)

if __name__ == '__main__':
    main()