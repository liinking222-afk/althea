#!/usr/bin/env python3
import re
import json
import subprocess
from pathlib import Path
from typing import Any, Dict, List

class PolyglotRegistry:
    def __init__(self, store_path="/tmp/althea_polyglot"):
        self.store = Path(store_path)
        self.store.mkdir(exist_ok=True)
        self.manifest = self.store / "manifest.json"
        self.modules = self._load_manifest()
    
    def _load_manifest(self) -> Dict:
        return json.loads(self.manifest.read_text()) if self.manifest.exists() else {}
    
    def _save_manifest(self):
        self.manifest.write_text(json.dumps(self.modules, indent=2))
    
    def register(self, code: str, metadata: Dict[str, Any] = None):
        lang_match = re.search(r'^(?:LANGUAGE:|#!.*?(?:python|node|bash|ruby))', code, re.M)
        intent_match = re.search(r'INTENT:\s*(.+?)$', code, re.M)
        
        capabilities = re.findall(r'def\s+(\w+)|function\s+(\w+)|class\s+(\w+)', code)
        caps = [c for group in capabilities for c in group if c]
        
        lang = "python" if "python" in (lang_match.group(0) if lang_match else "") else "bash"
        module_id = f"{intent_match.group(1)[:20] if intent_match else 'module'}_{len(self.modules)}"
        module_id = re.sub(r'\W+', '_', module_id)
        
        ext = {"python": "py", "bash": "sh", "javascript": "js"}.get(lang, "txt")
        module_path = self.store / f"{module_id}.{ext}"
        module_path.write_text(code)
        module_path.chmod(0o755)
        
        self.modules[module_id] = {
            "path": str(module_path),
            "language": lang,
            "capabilities": caps,
            "metadata": metadata or {}
        }
        self._save_manifest()
        return module_id
    
    def __getattr__(self, name: str):
        for mod_id, mod_info in self.modules.items():
            if name in mod_info["capabilities"] or re.search(name, mod_id, re.I):
                return lambda *args, **kwargs: self._invoke(mod_info["path"], *args)
        raise AttributeError(f"No module with capability '{name}'")
    
    def _invoke(self, path: str, *args):
        result = subprocess.run([path] + [str(a) for a in args], 
                              capture_output=True, text=True)
        return result.stdout.strip() if result.returncode == 0 else result.stderr

registry = PolyglotRegistry()