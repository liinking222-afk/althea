#!/usr/bin/env python3
import sys
import json
import subprocess
from pathlib import Path
from typing import Optional, Dict, Any

class ModulePipe:
    """UNIX-style pipe interface for Althea module composition"""
    
    def __init__(self, module_dir: str = "./modules"):
        self.module_dir = Path(module_dir)
    
    def invoke(self, module_name: str, input_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Invoke a module with JSON input, receive JSON output"""
        module_path = self.module_dir / f"{module_name}.py"
        
        if not module_path.exists():
            return {"error": f"Module {module_name} not found"}
        
        input_json = json.dumps(input_data or {})
        
        try:
            result = subprocess.run(
                [sys.executable, str(module_path)],
                input=input_json,
                capture_output=True,
                text=True,
                timeout=30
            )
            return json.loads(result.stdout) if result.stdout else {"error": result.stderr}
        except Exception as e:
            return {"error": str(e)}
    
    def pipeline(self, *module_names: str, input_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Chain modules in a pipeline: output of one becomes input of next"""
        data = input_data or {}
        
        for module in module_names:
            data = self.invoke(module, data)
            if "error" in data:
                return data
        
        return data

def main():
    """CLI interface: cat data.json | python module_pipe.py module1 module2"""
    pipe = ModulePipe()
    
    if len(sys.argv) < 2:
        print(json.dumps({"error": "Usage: module_pipe.py <module1> [module2] ..."}))
        sys.exit(1)
    
    input_data = json.load(sys.stdin) if not sys.stdin.isatty() else {}
    result = pipe.pipeline(*sys.argv[1:], input_data=input_data)
    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    main()