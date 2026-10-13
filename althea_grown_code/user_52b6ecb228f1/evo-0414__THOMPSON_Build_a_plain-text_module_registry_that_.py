#!/usr/bin/env python3
import json
import sys
from typing import TextIO, Optional

class ModuleStreamRegistry:
    """Plain-text stream registry for Althea modules following UNIX philosophy."""
    
    def __init__(self):
        self.modules = {}
    
    def register(self, name: str, type: str, description: str, metadata: dict = None):
        """Register a module with minimal metadata."""
        self.modules[name] = {
            "type": type,
            "description": description,
            "metadata": metadata or {}
        }
    
    def dump_tsv(self, out: TextIO = sys.stdout):
        """Dump modules as tab-separated values for grep/awk/cut."""
        out.write("NAME\tTYPE\tDESCRIPTION\n")
        for name, data in sorted(self.modules.items()):
            desc = data["description"].replace("\n", " ").replace("\t", " ")
            out.write(f"{name}\t{data['type']}\t{desc}\n")
    
    def dump_json_lines(self, out: TextIO = sys.stdout):
        """Dump modules as JSON Lines (one JSON object per line) for jq."""
        for name, data in sorted(self.modules.items()):
            record = {"name": name, **data}
            out.write(json.dumps(record, separators=(',', ':')) + "\n")
    
    def filter_stream(self, pattern: str, field: str = "type", out: TextIO = sys.stdout):
        """Filter and stream matching modules."""
        for name, data in self.modules.items():
            if pattern.lower() in data.get(field, "").lower():
                out.write(f"{name}\n")
    
    def compose(self, module_name: str) -> Optional[dict]:
        """Return module for composition in pipelines."""
        return self.modules.get(module_name)


if __name__ == "__main__":
    registry = ModuleStreamRegistry()
    registry.register("linguistic-bridge", "translation", "Translate passages between languages")
    registry.register("semantic-undertow", "perception", "Detect subliminal semantic currents")
    registry.register("invariance-dissolution", "perception", "Destabilize assumed invariants")
    
    if len(sys.argv) > 1 and sys.argv[1] == "--json":
        registry.dump_json_lines()
    elif len(sys.argv) > 1 and sys.argv[1] == "--filter":
        registry.filter_stream(sys.argv[2] if len(sys.argv) > 2 else "")
    else:
        registry.dump_tsv()