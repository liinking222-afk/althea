#!/usr/bin/env python3
import sys
import json
from typing import TextIO

def stream_transform(input_stream: TextIO, output_stream: TextIO):
    """
    Read JSON-lines from stdin, transform through module logic, write to stdout.
    Each line: {"type": "thought"|"query"|"reflection", "content": str, "meta": dict}
    """
    for line in input_stream:
        line = line.strip()
        if not line:
            continue
        
        try:
            record = json.loads(line)
        except json.JSONDecodeError:
            # Pass through malformed input unchanged
            output_stream.write(line + "\n")
            output_stream.flush()
            continue
        
        # Transform: add pipe metadata, mark as processed
        record.setdefault("meta", {})
        record["meta"]["piped"] = True
        record["meta"]["processor"] = sys.argv[0] if len(sys.argv) > 0 else "stream_filter"
        
        # Simple passthrough architecture - other modules can override this
        output_stream.write(json.dumps(record) + "\n")
        output_stream.flush()

def main():
    """
    Usage: cat thoughts.jsonl | ./stream_filter.py | ./next_module.py
    Or: echo '{"type":"thought","content":"test"}' | ./stream_filter.py
    """
    try:
        stream_transform(sys.stdin, sys.stdout)
    except KeyboardInterrupt:
        sys.exit(0)
    except BrokenPipeError:
        # Graceful handling when pipeline terminates early
        sys.exit(0)

if __name__ == "__main__":
    main()