#!/usr/bin/env python3
import json
import sys
from datetime import datetime
from typing import Dict, List, Optional

class ModuleRegistry:
    """Plain-text module registry following UNIX philosophy: emit streams, compose with pipes."""
    
    def __init__(self):
        self.modules: List[Dict] = []
    
    def register(self, name: str, type: str, version: str, tags: List[str], metadata: Optional[Dict] = None):
        """Register a module, emit NDJSON line to stdout."""
        entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "name": name,
            "type": type,
            "version": version,
            "tags": tags,
            "metadata": metadata or {}
        }
        self.modules.append(entry)
        print(json.dumps(entry), flush=True)
    
    def list(self, filter_type: Optional[str] = None, filter_tag: Optional[str] = None):
        """Emit filtered module stream as NDJSON."""
        for module in self.modules:
            if filter_type and module["type"] != filter_type:
                continue
            if filter_tag and filter_tag not in module["tags"]:
                continue
            print(json.dumps(module), flush=True)
    
    def grep(self, pattern: str):
        """Stream modules matching pattern in name or tags."""
        for module in self.modules:
            if pattern in module["name"] or any(pattern in tag for tag in module["tags"]):
                print(json.dumps(module), flush=True)

def main():
    """CLI interface for shell composition."""
    if len(sys.argv) < 2:
        print("Usage: registry.py [register|list|grep] [args...]", file=sys.stderr)
        sys.exit(1)
    
    registry = ModuleRegistry()
    cmd = sys.argv[1]
    
    if cmd == "register" and len(sys.argv) >= 5:
        name, type_, version = sys.argv[2], sys.argv[3], sys.argv[4]
        tags = sys.argv[5].split(",") if len(sys.argv) > 5 else []
        registry.register(name, type_, version, tags)
    elif cmd == "list":
        filter_type = sys.argv[2] if len(sys.argv) > 2 else None
        registry.list(filter_type=filter_type)
    elif cmd == "grep" and len(sys.argv) > 2:
        registry.grep(sys.argv[2])

if __name__ == "__main__":
    main()