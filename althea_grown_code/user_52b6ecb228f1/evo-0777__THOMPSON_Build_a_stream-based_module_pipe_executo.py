#!/usr/bin/env python3
import sys
import json
import subprocess
from pathlib import Path
from typing import Iterator, Any, Dict

class ModulePipe:
    """UNIX-style pipe compositor for Althea modules using JSON-lines."""
    
    def __init__(self, modules_dir: Path = Path("/tmp/althea_modules")):
        self.modules_dir = modules_dir
        self.modules_dir.mkdir(exist_ok=True)
    
    def stream_json(self, data: Iterator[Dict[str, Any]]) -> Iterator[str]:
        """Convert iterator of dicts to JSON-lines."""
        for item in data:
            yield json.dumps(item) + "\n"
    
    def parse_json_stream(self, stream) -> Iterator[Dict[str, Any]]:
        """Parse JSON-lines from stream."""
        for line in stream:
            line = line.strip()
            if line:
                try:
                    yield json.loads(line)
                except json.JSONDecodeError:
                    continue
    
    def pipe(self, module_a: str, module_b: str, input_data: Iterator[Dict]) -> Iterator[Dict]:
        """Pipe data through two modules: input → A → B → output."""
        
        # Start module A
        proc_a = subprocess.Popen(
            [module_a],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        # Start module B
        proc_b = subprocess.Popen(
            [module_b],
            stdin=proc_a.stdout,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        # Feed input to A
        for line in self.stream_json(input_data):
            proc_a.stdin.write(line)
        proc_a.stdin.close()
        
        # Read output from B
        yield from self.parse_json_stream(proc_b.stdout)
        
        proc_b.wait()
        proc_a.wait()
    
    def chain(self, *modules: str, input_data: Iterator[Dict]) -> Iterator[Dict]:
        """Chain N modules together via pipes."""
        if not modules:
            yield from input_data
            return
        
        if len(modules) == 1:
            yield from self._run_single(modules[0], input_data)
            return
        
        # Recursive pipe composition
        mid_data = self._run_single(modules[0], input_data)
        yield from self.chain(*modules[1:], input_data=mid_data)
    
    def _run_single(self, module: str, input_data: Iterator[Dict]) -> Iterator[Dict]:
        """Run single module with input."""
        proc = subprocess.Popen(
            [module],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            text=True
        )
        
        for line in self.stream_json(input_data):
            proc.stdin.write(line)
        proc.stdin.close()
        
        yield from self.parse_json_stream(proc.stdout)

if __name__ == "__main__":
    pipe = ModulePipe()
    test_data = iter([{"x": 1}, {"x": 2}, {"x": 3}])
    for result in pipe.chain(sys.argv[1], sys.argv[2], input_data=test_data):
        print(json.dumps(result))