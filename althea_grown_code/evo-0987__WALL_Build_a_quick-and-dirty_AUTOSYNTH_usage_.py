#!/usr/bin/env python3
import re
import sys
from collections import Counter, defaultdict
from datetime import datetime

AUTOSYNTH_PATTERN = r'\[AUTOSYNTH\s+(/[\w-]+)\]\s+([^\(]+)\s*\([^\)]+\)\.\s+(.+?)(?:\s+—|$)'
EVO_PATTERN = r'\[EVO\s+#(\d+)\s+(\w+)\s+v([\d\.]+)→v([\d\.]+)\]'

def parse_stream(stream):
    autosynth_calls = Counter()
    autosynth_details = defaultdict(list)
    evo_events = []
    
    for line in stream:
        line = line.strip()
        
        # Match AUTOSYNTH invocations
        match = re.search(AUTOSYNTH_PATTERN, line)
        if match:
            path, desc, context = match.groups()
            autosynth_calls[path] += 1
            autosynth_details[path].append(desc.strip())
        
        # Match EVO events
        evo_match = re.search(EVO_PATTERN, line)
        if evo_match:
            num, arch, old_v, new_v = evo_match.groups()
            evo_events.append((num, arch, old_v, new_v))
    
    return autosynth_calls, autosynth_details, evo_events

def emit_report(calls, details, evos):
    print("=== AUTOSYNTH FREQUENCY REPORT ===\n")
    
    if calls:
        print(f"Total invocations: {sum(calls.values())}")
        print(f"Unique modules: {len(calls)}\n")
        
        for path, count in calls.most_common(10):
            print(f"{count:3d}  {path}")
            desc = details[path][0] if details[path] else "N/A"
            print(f"     └─ {desc}\n")
    
    if evos:
        print("\n=== RECENT EVOLUTIONS ===\n")
        for num, arch, old, new in evos[-5:]:
            print(f"#{num} {arch:12s} {old} → {new}")

def emit_tsv(calls):
    print("path\tcount")
    for path, count in calls.most_common():
        print(f"{path}\t{count}")

if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "report"
    calls, details, evos = parse_stream(sys.stdin)
    
    if mode == "tsv":
        emit_tsv(calls)
    else:
        emit_report(calls, details, evos)