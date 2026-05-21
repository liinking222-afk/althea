#!/usr/bin/env python3
import re
import sys

def extract_memory_count(line):
    """Parse memory_count from SELF-VISION line."""
    match = re.search(r'memory_count=(\d+)', line)
    return int(match.group(1)) if match else None

def validate_monotonic(counts):
    """Check if sequence is monotonically non-decreasing."""
    violations = []
    for i in range(1, len(counts)):
        if counts[i] < counts[i-1]:
            violations.append((i-1, counts[i-1], i, counts[i]))
    return violations

def main():
    lines = sys.stdin.readlines()
    
    counts = []
    timestamps = []
    
    for idx, line in enumerate(lines):
        if '[SELF-VISION]' in line:
            count = extract_memory_count(line)
            if count is not None:
                counts.append(count)
                timestamps.append(idx)
    
    if len(counts) < 2:
        print("MONOTONIC: insufficient data")
        return 0
    
    violations = validate_monotonic(counts)
    
    if not violations:
        print(f"MONOTONIC: verified {len(counts)} observations [{counts[0]}→{counts[-1]}]")
        return 0
    else:
        print(f"CAUSAL_VIOLATION: {len(violations)} detected")
        for prev_idx, prev_count, curr_idx, curr_count in violations:
            print(f"  position {prev_idx}→{curr_idx}: {prev_count}→{curr_count} (delta: {curr_count - prev_count})")
        return 1

if __name__ == '__main__':
    sys.exit(main())