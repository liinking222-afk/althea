#!/usr/bin/env python3
import sys
import json
import subprocess
from pathlib import Path

def load_module_registry():
    """Load available modules from registry."""
    registry_path = Path.home() / ".althea" / "module_registry.json"
    if registry_path.exists():
        with open(registry_path) as f:
            return json.load(f)
    return {}

def execute_module(module_name, input_data):
    """Execute a module with input, return output as text."""
    registry = load_module_registry()
    if module_name not in registry:
        raise ValueError(f"Module {module_name} not found")
    
    module_path = registry[module_name]["path"]
    proc = subprocess.Popen(
        [sys.executable, module_path],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    stdout, stderr = proc.communicate(input=input_data)
    if proc.returncode != 0:
        raise RuntimeError(f"Module failed: {stderr}")
    return stdout

def main():
    if len(sys.argv) < 2:
        print("Usage: pipe <module1> <module2> ... < input.txt", file=sys.stderr)
        sys.exit(1)
    
    modules = sys.argv[1:]
    data = sys.stdin.read()
    
    for module in modules:
        data = execute_module(module, data)
    
    sys.stdout.write(data)

if __name__ == "__main__":
    main()