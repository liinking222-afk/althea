#!/usr/bin/env python3
import re
import json
import sys
from pathlib import Path
from typing import List, Dict, Any

class ModuleQuery:
    def __init__(self, registry_path: str = "/tmp/althea_modules.json"):
        self.registry_path = Path(registry_path)
        self.modules = self._load_registry()
    
    def _load_registry(self) -> List[Dict[str, Any]]:
        if not self.registry_path.exists():
            return []
        try:
            with open(self.registry_path) as f:
                return json.load(f)
        except:
            return []
    
    def query(self, pattern: str = ".*", tag: str = None) -> List[Dict[str, Any]]:
        results = []
        regex = re.compile(pattern, re.IGNORECASE)
        
        for mod in self.modules:
            name = mod.get("name", "")
            desc = mod.get("description", "")
            tags = mod.get("tags", [])
            
            if regex.search(name) or regex.search(desc):
                if tag is None or tag in tags:
                    results.append(mod)
        
        return results
    
    def format(self, results: List[Dict], fmt: str = "human") -> str:
        if fmt == "json":
            return json.dumps(results, indent=2)
        elif fmt == "tsv":
            lines = ["NAME\tVERSION\tDESCRIPTION"]
            for r in results:
                lines.append(f"{r.get('name', 'N/A')}\t{r.get('version', 'N/A')}\t{r.get('description', 'N/A')}")
            return "\n".join(lines)
        else:  # human
            if not results:
                return "No modules found."
            lines = []
            for r in results:
                lines.append(f"• {r.get('name', 'N/A')} v{r.get('version', 'N/A')}")
                lines.append(f"  {r.get('description', 'N/A')}")
            return "\n".join(lines)

def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("pattern", nargs="?", default=".*")
    parser.add_argument("-t", "--tag", help="Filter by tag")
    parser.add_argument("-f", "--format", choices=["json", "tsv", "human"], default="human")
    parser.add_argument("-r", "--registry", default="/tmp/althea_modules.json")
    
    args = parser.parse_args()
    
    mq = ModuleQuery(args.registry)
    results = mq.query(args.pattern, args.tag)
    print(mq.format(results, args.format))

if __name__ == "__main__":
    main()