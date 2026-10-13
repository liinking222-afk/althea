#!/usr/bin/env python3
import sys
import json
import importlib
import os

REGISTRY = {}

def register_module(name, handler_path):
    """Register a module: name -> module.function"""
    REGISTRY[name] = handler_path

def load_handler(handler_path):
    """Load module.function from string like 'orbital_propagation.compute'"""
    module_name, func_name = handler_path.rsplit('.', 1)
    mod = importlib.import_module(module_name)
    return getattr(mod, func_name)

def dispatch(line):
    """Parse line: 'MODULE_NAME {json_args}' and invoke handler"""
    line = line.strip()
    if not line or line.startswith('#'):
        return None
    
    parts = line.split(None, 1)
    if len(parts) == 0:
        return None
    
    module_name = parts[0]
    args_json = parts[1] if len(parts) > 1 else '{}'
    
    if module_name not in REGISTRY:
        return json.dumps({"error": f"unknown_module: {module_name}"})
    
    try:
        args = json.loads(args_json)
        handler = load_handler(REGISTRY[module_name])
        result = handler(**args)
        return json.dumps({"module": module_name, "result": result})
    except Exception as e:
        return json.dumps({"error": str(e), "module": module_name})

def load_registry():
    """Load registry from MODULE_REGISTRY env or .modules file"""
    reg_file = os.environ.get('MODULE_REGISTRY', '.modules')
    if os.path.exists(reg_file):
        with open(reg_file) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    name, path = line.split(None, 1)
                    register_module(name, path)

def main():
    load_registry()
    
    for line in sys.stdin:
        output = dispatch(line)
        if output:
            print(output, flush=True)

if __name__ == '__main__':
    main()