import json
from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict
from datetime import datetime

@dataclass
class ModuleMetrics:
    name: str
    category: str
    token_cost: int
    dependencies: List[str]
    last_invoked: Optional[str]
    invocation_count: int
    avg_execution_ms: float

class CapabilityRegistry:
    def __init__(self, registry_path: str = ".althea/capability_registry.json"):
        self.registry_path = Path(registry_path)
        self.registry_path.parent.mkdir(parents=True, exist_ok=True)
        self.modules: Dict[str, ModuleMetrics] = self._load()
    
    def _load(self) -> Dict[str, ModuleMetrics]:
        if self.registry_path.exists():
            data = json.loads(self.registry_path.read_text())
            return {k: ModuleMetrics(**v) for k, v in data.items()}
        return {}
    
    def _save(self):
        data = {k: asdict(v) for k, v in self.modules.items()}
        self.registry_path.write_text(json.dumps(data, indent=2))
    
    def register(self, name: str, category: str, token_cost: int, 
                 dependencies: List[str] = None):
        self.modules[name] = ModuleMetrics(
            name=name, category=category, token_cost=token_cost,
            dependencies=dependencies or [], last_invoked=None,
            invocation_count=0, avg_execution_ms=0.0
        )
        self._save()
    
    def record_invocation(self, name: str, execution_ms: float):
        if name in self.modules:
            m = self.modules[name]
            m.invocation_count += 1
            m.avg_execution_ms = (m.avg_execution_ms * (m.invocation_count - 1) + 
    execution_ms) / m.invocation_count
            m.last_invoked = datetime.utcnow().isoformat()
            self._save()
    
    def get_total_cost(self, modules: List[str]) -> int:
        visited = set()
        def recurse(name: str) -> int:
            if name in visited or name not in self.modules:
                return 0
            visited.add(name)
            m = self.modules[name]
            return m.token_cost + sum(recurse(d) for d in m.dependencies)
        return sum(recurse(m) for m in modules)
    
    def find_underutilized(self, threshold: int = 3) -> List[str]:
        return [m.name for m in self.modules.values() 
                if m.invocation_count < threshold]
    
    def estimate_budget_remaining(self, budget: int, proposed: List[str]) -> int:
        return budget - self.get_total_cost(proposed)

registry = CapabilityRegistry()