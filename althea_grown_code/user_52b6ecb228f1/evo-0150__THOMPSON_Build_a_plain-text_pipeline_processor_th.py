#!/usr/bin/env python3
import sys
import json
import importlib.util
from pathlib import Path

def load_module(module_path):
    """Load a module from file path."""
    spec = importlib.util.spec_from_file_location("pipeline_module", module_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

def stream_pipeline(modules, input_stream=sys.stdin):
    """Process stdin through a chain of modules, each outputting to next."""
    current_data = input_stream.read()
    
    for module_path in modules:
        module = load_module(module_path)
        
        # Each module must have a process() function
        if hasattr(module, 'process'):
            current_data = module.process(current_data)
        else:
            sys.stderr.write(f"Warning: {module_path} has no process() function\n")
    
    return current_data

def main():
    if len(sys.argv) < 2:
        sys.stderr.write("Usage: pipeline.py <module1.py> [module2.py ...]\n")
        sys.stderr.write("Pipes data through modules left-to-right.\n")
        sys.stderr.write("Each module must have process(input_str) -> output_str\n")
        sys.exit(1)
    
    module_paths = sys.argv[1:]
    
    # Validate all modules exist
    for path in module_paths:
        if not Path(path).exists():
            sys.stderr.write(f"Error: Module not found: {path}\n")
            sys.exit(1)
    
    # Execute pipeline
    result = stream_pipeline(module_paths)
    sys.stdout.write(result)
    sys.stdout.flush()

if __name__ == "__main__":
    main()