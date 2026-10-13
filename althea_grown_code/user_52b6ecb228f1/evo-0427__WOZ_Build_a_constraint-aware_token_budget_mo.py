import re
from dataclasses import dataclass
from typing import Optional

@dataclass
class TokenBudget:
    """Woz-style: make every token count."""
    total: int
    consumed: int = 0
    
    @property
    def remaining(self) -> int:
        return max(0, self.total - self.consumed)
    
    @property
    def utilization(self) -> float:
        return self.consumed / self.total if self.total > 0 else 0.0
    
    @property
    def efficiency_zone(self) -> str:
        """Hardware-inspired efficiency bands."""
        u = self.utilization
        if u < 0.5: return "UNDERUTILIZED"
        if u < 0.8: return "OPTIMAL"
        if u < 0.95: return "CONSTRAINED"
        return "CRITICAL"
    
    def consume(self, tokens: int) -> bool:
        """Return False if budget exceeded."""
        if self.consumed + tokens > self.total:
            return False
        self.consumed += tokens
        return True
    
    def status(self) -> str:
        bar_width = 20
        filled = int(self.utilization * bar_width)
        bar = "█" * filled + "░" * (bar_width - filled)
        return f"[{bar}] {self.consumed}/{self.total} ({self.utilization*100:.1f}%) {self.efficiency_zone}"


class BudgetMonitor:
    """Extract budget from context, track across operations."""
    
    def __init__(self, context: str):
        self.budget = self._extract_budget(context)
    
    def _extract_budget(self, context: str) -> Optional[TokenBudget]:
        match = re.search(r'<budget:token_budget>(\d+)</budget:token_budget>', context)
        if match:
            return TokenBudget(total=int(match.group(1)))
        return None
    
    def track(self, operation: str, tokens: int) -> str:
        if not self.budget:
            return f"{operation}: {tokens} tokens (no budget set)"
        
        success = self.budget.consume(tokens)
        status = "✓" if success else "✗ EXCEEDED"
        return f"{operation}: {tokens}t {status} | {self.budget.status()}"