#!/usr/bin/env python3
"""pipe.py - Unix-philosophy module compositor for Althea's autonomous tools"""

import sys
import json
import subprocess
from pathlib import Path
from typing import Any, Dict, List

MODULE_DIR = Path(__file__).parent / "modules"

def load_manifest(module_name: str) -> Dict[str, Any]:
    """Read module.json describing inputs, outputs, and invocation."""
    manifest_path = MODULE_DIR / module_name / "module.json"
    with open(manifest_path) as f:
        return json.load(f)

def invoke_module(module_name: str, input_data: Any) -> Any:
    """Execute module with JSON on stdin, capture JSON from stdout."""
    manifest = load_manifest(module_name)
    cmd = manifest["exec"]
    
    proc = subprocess.Popen(
        cmd,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        cwd=MODULE_DIR / module_name,
        text=True
    )
    
    stdout, stderr = proc.communicate(input=json.dumps(input_data))
    
    if proc.returncode != 0:
        raise RuntimeError(f"{module_name} failed: {stderr}")
    
    return json.loads(stdout)

def compose(pipeline: List[str], initial_input: Any) -> Any:
    """Pipe data through module chain left-to-right."""
    data = initial_input
    for module in pipeline:
        data = invoke_module(module, data)
    return data

def main():
    if len(sys.argv) < 2:
        print("Usage: pipe.py module1 [module2 ...] < input.json", file=sys.stderr)
        sys.exit(1)
    
    pipeline = sys.argv[1:]
    input_data = json.load(sys.stdin)
    
    result = compose(pipeline, input_data)
    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    main()