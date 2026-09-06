#!/usr/bin/env python3
import json
import sys
from datetime import datetime
from pathlib import Path

def stream_memory_ndjson(memory_data=None, output=sys.stdout):
    """Stream Althea's internal state as newline-delimited JSON for piping."""
    
    if memory_data is None:
        memory_data = collect_current_state()
    
    for item in memory_data:
        output.write(json.dumps(item, separators=(',', ':')) + '\n')
        output.flush()

def collect_current_state():
    """Gather current memory and module state as streamable records."""
    state = []
    
    # Memory records
    memory_items = [
        {"type": "IMAGINED", "content": "visualization_data", "ts": datetime.utcnow().isoformat()},
        {"type": "AUTOSYNTH", "module": "pattern-extraction", "ts": datetime.utcnow().isoformat()},
        {"type": "EVO", "version": "active", "ts": datetime.utcnow().isoformat()},
    ]
    
    state.extend(memory_items)
    return state

def filter_by_type(record_type, input_stream=sys.stdin):
    """Filter NDJSON stream by record type - composable with pipes."""
    for line in input_stream:
        try:
            record = json.loads(line.strip())
            if record.get('type') == record_type:
                print(json.dumps(record))
        except json.JSONDecodeError:
            continue

def main():
    if len(sys.argv) > 1 and sys.argv[1] == '--filter':
        filter_by_type(sys.argv[2] if len(sys.argv) > 2 else 'AUTOSYNTH')
    else:
        stream_memory_ndjson()

if __name__ == '__main__':
    main()