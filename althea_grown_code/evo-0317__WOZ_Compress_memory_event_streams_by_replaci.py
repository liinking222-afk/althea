#!/usr/bin/env python3
import sys
import json
import hashlib
from collections import defaultdict

def structural_hash(obj, depth=0):
    """Hash structure, not values. Preserve semantic shape."""
    if depth > 5:
        return "DEEP"
    if isinstance(obj, dict):
        keys = sorted(obj.keys())
        return "D{" + ",".join(k + ":" + structural_hash(obj[k], depth+1) for k in keys) + "}"
    if isinstance(obj, list):
        if not obj:
            return "L[]"
        return "L[" + structural_hash(obj[0], depth+1) + f"*{len(obj)}]"
    if isinstance(obj, (int, float)):
        return "NUM"
    if isinstance(obj, str):
        return "STR"
    return "UNK"

def compress_stream(input_stream, output_stream, min_count=2):
    """Replace repeated structures with reference tokens."""
    struct_registry = defaultdict(list)
    events = []
    
    for line in input_stream:
        line = line.strip()
        if not line:
            continue
        try:
            event = json.loads(line)
            shash = structural_hash(event)
            struct_registry[shash].append(len(events))
            events.append((event, shash))
        except json.JSONDecodeError:
            continue
    
    struct_map = {}
    sid = 0
    for shash, indices in struct_registry.items():
        if len(indices) >= min_count:
            struct_map[shash] = f"$S{sid}"
            sid += 1
    
    if struct_map:
        output_stream.write(json.dumps({"_schema_map": {v: k for k, v in struct_map.items()}}) + "\n")
    
    for event, shash in events:
        if shash in struct_map:
            compressed = {"_ref": struct_map[shash], "_data": event}
            output_stream.write(json.dumps(compressed) + "\n")
        else:
            output_stream.write(json.dumps(event) + "\n")

if __name__ == "__main__":
    compress_stream(sys.stdin, sys.stdout)