#!/usr/bin/env python3
import sys
import json
import subprocess
from pathlib import Path
from typing import Dict, Any, List

class StreamCompositor:
    """UNIX-style module compositor for Althea's runtime."""
    
    def __init__(self, modules_dir: str = "./modules"):
        self.modules_dir = Path(modules_dir)
    
    def pipe(self, pipeline: List[Dict[str, Any]], input_data: str = "") -> str:
        """Execute a pipeline of modules, piping stdout to stdin."""
        current_input = input_data.encode('utf-8')
        
        for stage in pipeline:
            module_name = stage.get("module")
            args = stage.get("args", [])
            
            module_path = self.modules_dir / f"{module_name}.py"
            if not module_path.exists():
                module_path = self.modules_dir / module_name
            
            cmd = [sys.executable, str(module_path)] + args
            
            proc = subprocess.Popen(
                cmd,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            
            stdout, stderr = proc.communicate(input=current_input)
            
            if proc.returncode != 0:
                raise RuntimeError(f"Module {module_name} failed: {stderr.decode()}")
            
            current_input = stdout
        
        return current_input.decode('utf-8')
    
    def compose(self, pipeline_spec: str) -> str:
        """Parse and execute a pipeline from JSON or shell-style spec."""
        if pipeline_spec.strip().startswith('['):
            pipeline = json.loads(pipeline_spec)
        else:
            # Simple shell-style: "module1 | module2 --arg | module3"
            stages = [s.strip() for s in pipeline_spec.split('|')]
            pipeline = []
            for stage in stages:
                parts = stage.split()
                pipeline.append({"module": parts[0], "args": parts[1:]})
        
        return self.pipe(pipeline)

if __name__ == "__main__":
    compositor = StreamCompositor()
    
    if len(sys.argv) > 1:
        pipeline_spec = ' '.join(sys.argv[1:])
        input_data = sys.stdin.read()
        result = compositor.compose(pipeline_spec)
        print(result, end='')
    else:
        print("Usage: echo 'data' | compositor.py 'module1 | module2 | module3'")