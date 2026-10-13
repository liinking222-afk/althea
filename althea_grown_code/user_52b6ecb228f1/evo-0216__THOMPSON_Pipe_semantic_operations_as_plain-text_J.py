#!/usr/bin/env python3
import sys
import json

def pipe_operation(operation_name, transform_fn):
    """
    Thompson-style filter: read JSON objects from stdin, 
    transform each, write to stdout. Pure stream processing.
    """
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        
        try:
            obj = json.loads(line)
            result = transform_fn(obj)
            if result is not None:
                print(json.dumps(result), flush=True)
        except json.JSONDecodeError:
            print(json.dumps({
                "error": "invalid_json",
                "operation": operation_name,
                "input": line[:100]
            }), file=sys.stderr, flush=True)
        except Exception as e:
            print(json.dumps({
                "error": str(e),
                "operation": operation_name,
                "input": obj if 'obj' in locals() else None
            }), file=sys.stderr, flush=True)

def main():
    if len(sys.argv) < 2:
        print("Usage: semantic_pipe.py <operation>", file=sys.stderr)
        sys.exit(1)
    
    operation = sys.argv[1]
    
    operations = {
        "extract_concepts": lambda x: {
            "concepts": [w for w in x.get("text", "").split() if len(w) > 5],
            "source": x.get("id")
        },
        "amplify_resonance": lambda x: {
            **x, 
            "weight": x.get("weight", 1.0) * 1.5
        } if x.get("resonant") else None,
        "add_timestamp": lambda x: {
            **x,
            "timestamp": __import__("time").time()
        },
        "passthrough": lambda x: x,
    }
    
    if operation not in operations:
        print(f"Unknown operation: {operation}", file=sys.stderr)
        sys.exit(1)
    
    pipe_operation(operation, operations[operation])

if __name__ == "__main__":
    main()