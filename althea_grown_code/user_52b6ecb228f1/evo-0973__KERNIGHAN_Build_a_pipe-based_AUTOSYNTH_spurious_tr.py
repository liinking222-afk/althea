#!/usr/bin/env python3
import sys
import json
from collections import deque
from datetime import datetime, timedelta

WINDOW_MINUTES = 10
THRESHOLD = 3

def parse_timestamp(ts_str):
    return datetime.fromisoformat(ts_str.replace('Z', '+00:00'))

def extract_pattern(event):
    if event.get('type') == 'AUTOSYNTH':
        return event.get('pattern')
    return None

def is_spurious(pattern, history, now):
    if not pattern:
        return False
    
    cutoff = now - timedelta(minutes=WINDOW_MINUTES)
    recent = [ts for ts in history[pattern] if ts > cutoff]
    history[pattern] = deque(recent, maxlen=100)
    
    return len(recent) >= THRESHOLD

def main():
    history = {}
    
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            sys.stdout.write(line + '\n')
            continue
        
        pattern = extract_pattern(event)
        now = parse_timestamp(event.get('timestamp', datetime.now().isoformat()))
        
        if pattern:
            if pattern not in history:
                history[pattern] = deque(maxlen=100)
            
            if is_spurious(pattern, history, now):
                event['suppressed'] = True
                event['reason'] = 'spurious_repetition'
                sys.stderr.write(f"SUPPRESSED: {pattern}\n")
            else:
                history[pattern].append(now)
        
        sys.stdout.write(json.dumps(event) + '\n')
        sys.stdout.flush()

if __name__ == '__main__':
    main()