#!/usr/bin/env python3
import json
import subprocess
import sys
from pathlib import Path
import re

class PolyglotExecutor:
    RUNTIME_MAP = {
        'py': ['python3'],
        'js': ['node'],
        'sh': ['bash'],
        'rb': ['ruby'],
        'pl': ['perl'],
        'lua': ['lua'],
        'php': ['php'],
    }
    
    SHEBANG_PATTERN = re.compile(r'^#!\s*(?:/usr/bin/env\s+)?(\S+)')
    
    def detect_runtime(self, module_path):
        path = Path(module_path)
        
        # Try shebang first (Wall-style: examine the artifact)
        try:
            with open(path, 'r') as f:
                first_line = f.readline()
                match = self.SHEBANG_PATTERN.match(first_line)
                if match:
                    interpreter = Path(match.group(1)).name
                    return [interpreter]
        except:
            pass
        
        # Fall back to extension
        ext = path.suffix.lstrip('.')
        return self.RUNTIME_MAP.get(ext, [path.as_posix()])
    
    def execute(self, module_path, input_data=None):
        runtime = self.detect_runtime(module_path)
        cmd = runtime + [str(module_path)]
        
        input_json = json.dumps(input_data) + '\n' if input_data else ''
        
        proc = subprocess.Popen(
            cmd,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        stdout, stderr = proc.communicate(input=input_json)
        
        results = []
        for line in stdout.strip().split('\n'):
            if line:
                try:
                    results.append(json.loads(line))
                except json.JSONDecodeError:
                    results.append({'raw': line})
        
        return {
            'exit_code': proc.returncode,
            'results': results,
            'stderr': stderr if stderr else None
        }

if __name__ == '__main__':
    executor = PolyglotExecutor()
    input_data = json.loads(sys.stdin.read()) if not sys.stdin.isatty() else None
    
    module = sys.argv[1] if len(sys.argv) > 1 else input_data.get('module')
    result = executor.execute(module, input_data)
    
    print(json.dumps(result))