#!/usr/bin/env python3
import sys
import json
import re

def parse_filter(filter_spec):
    """Parse filter specification like 'jq:.data.values' or 'grep:error' or 'head:10'"""
    if ':' not in filter_spec:
        return ('pass', filter_spec)
    cmd, arg = filter_spec.split(':', 1)
    return (cmd, arg)

def apply_filter(data, filter_type, arg):
    """Apply a single filter transformation to data stream"""
    if filter_type == 'jq':
        # Simple JSONPath-like extraction
        obj = json.loads(data) if isinstance(data, str) else data
        for key in arg.strip('.').split('.'):
            obj = obj.get(key, obj) if isinstance(obj, dict) else obj
        return json.dumps(obj) if not isinstance(obj, str) else obj
    
    elif filter_type == 'grep':
        lines = data.split('\n') if isinstance(data, str) else [data]
        return '\n'.join(line for line in lines if re.search(arg, line))
    
    elif filter_type == 'head':
        lines = data.split('\n') if isinstance(data, str) else [str(data)]
        return '\n'.join(lines[:int(arg)])
    
    elif filter_type == 'tail':
        lines = data.split('\n') if isinstance(data, str) else [str(data)]
        return '\n'.join(lines[-int(arg):])
    
    elif filter_type == 'sed':
        pattern, repl = arg.split('/', 1) if '/' in arg else (arg, '')
        return re.sub(pattern, repl, data)
    
    elif filter_type == 'wc':
        lines = data.split('\n') if isinstance(data, str) else [str(data)]
        return str(len(lines)) if arg == 'l' else str(len(data))
    
    elif filter_type == 'pass':
        return data
    
    return data

def main():
    if len(sys.argv) < 2:
        input_data = sys.stdin.read()
    else:
        input_data = sys.stdin.read()
    
    filters = sys.argv[1:] if len(sys.argv) > 1 else []
    
    result = input_data
    for filter_spec in filters:
        filter_type, arg = parse_filter(filter_spec)
        result = apply_filter(result, filter_type, arg)
    
    print(result, end='')

if __name__ == '__main__':
    main()