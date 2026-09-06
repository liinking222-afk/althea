#!/usr/bin/env python3
import json
import sys
from pathlib import Path
from typing import Callable, Dict, Any

class PipeRegistry:
    """Registry of single-purpose functions with stdin/stdout contracts."""
    
    def __init__(self):
        self.functions: Dict[str, Callable] = {}
        self.contracts: Dict[str, Dict[str, str]] = {}
    
    def register(self, name: str, input_type: str, output_type: str):
        """Decorator to register a pipe-composable function."""
        def decorator(func: Callable):
            self.functions[name] = func
            self.contracts[name] = {"input": input_type, "output": output_type}
            return func
        return decorator
    
    def validate_chain(self, chain: list[str]) -> bool:
        """Check if functions can pipe together by type compatibility."""
        for i in range(len(chain) - 1):
            out_type = self.contracts[chain[i]]["output"]
            in_type = self.contracts[chain[i + 1]]["input"]
            if out_type != in_type:
                return False
        return True
    
    def execute(self, name: str, input_data: Any) -> Any:
        """Execute one function with explicit input."""
        return self.functions[name](input_data)
    
    def pipe(self, chain: list[str], initial: Any) -> Any:
        """Compose functions left-to-right."""
        if not self.validate_chain(chain):
            raise ValueError(f"Type mismatch in chain: {chain}")
        result = initial
        for func_name in chain:
            result = self.execute(func_name, result)
        return result
    
    def list_tools(self) -> dict:
        """Show all registered tools and their contracts."""
        return {name: self.contracts[name] for name in self.functions}

# Global registry
registry = PipeRegistry()

@registry.register("parse_json", "text", "dict")
def parse_json(text: str) -> dict:
    return json.loads(text)

@registry.register("extract_field", "dict", "any")
def extract_field(data: dict) -> Any:
    key = data.get("_key", list(data.keys())[0])
    return data[key]

@registry.register("to_json", "any", "text")
def to_json(data: Any) -> str:
    return json.dumps(data, indent=2)

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "list":
        print(json.dumps(registry.list_tools(), indent=2))
    else:
        input_data = sys.stdin.read()
        chain = sys.argv[1:] if len(sys.argv) > 1 else ["parse_json", "to_json"]
        result = registry.pipe(chain, input_data)
        print(result)