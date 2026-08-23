#!/usr/bin/env python3
import json
import sys
from pathlib import Path
from typing import Iterator, Dict, Any

def stream_module_metadata(modules_dir: Path = Path("/modules")) -> Iterator[str]:
    """Stream each module as a single-line JSON object for pipeline processing."""
    
    if not modules_dir.exists():
        return
    
    for module_path in sorted(modules_dir.rglob("*.py")):
        try:
            with open(module_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Extract basic metadata without parsing AST (Thompson: simple tools)
            lines = content.split('\n')
            docstring = None
            for line in lines[:20]:
                if '"""' in line or "'''" in line:
                    docstring = line.strip('"""').strip("'''").strip()
                    break
            
            metadata = {
                "path": str(module_path.relative_to(modules_dir)),
                "name": module_path.stem,
                "lines": len(lines),
                "bytes": len(content),
                "doc": docstring or "",
                "imports": [l.strip() for l in lines if l.startswith('import ') or l.startswith('from ')][:5]
            }
            
            yield json.dumps(metadata, separators=(',', ':'))
            
        except Exception:
            continue

def main():
    """Emit line-delimited JSON to stdout for pipeline composition."""
    for line in stream_module_metadata():
        print(line, flush=True)

if __name__ == "__main__":
    main()