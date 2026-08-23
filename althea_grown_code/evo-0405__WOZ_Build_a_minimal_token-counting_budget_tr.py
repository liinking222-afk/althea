import re
from typing import Dict, Optional, Tuple

class TokenBudgetTracker:
    """Tracks token expenditure against declared budgets with minimal overhead."""
    
    def __init__(self):
        self.budgets: Dict[str, int] = {}
        self.spent: Dict[str, int] = {}
        self.warnings_issued: Dict[str, bool] = {}
    
    def parse_budget(self, text: str) -> Optional[Tuple[str, int]]:
        """Extract budget declarations from text using lean regex."""
        match = re.search(r'<budget:(\w+)>(\d+)</budget:\1>', text)
        if match:
            return match.group(1), int(match.group(2))
        return None
    
    def register_budget(self, budget_type: str, limit: int):
        """Set a budget limit."""
        self.budgets[budget_type] = limit
        self.spent[budget_type] = 0
        self.warnings_issued[budget_type] = False
    
    def add_spend(self, budget_type: str, amount: int) -> Optional[str]:
        """Record spend and return warning if threshold breached."""
        if budget_type not in self.budgets:
            return None
        
        self.spent[budget_type] += amount
        remaining = self.budgets[budget_type] - self.spent[budget_type]
        utilization = self.spent[budget_type] / self.budgets[budget_type]
        
        # Emit warning at 80% threshold, once
        if utilization >= 0.8 and not self.warnings_issued[budget_type]:
            self.warnings_issued[budget_type] = True
            return f"⚠ {budget_type}: {self.spent[budget_type]}/{self.budgets[budget_type]} ({utilization*100:.0f}%) — {remaining} remaining"
        
        if remaining < 0:
            return f"🔴 {budget_type}: EXCEEDED by {abs(remaining)}"
        
        return None
    
    def get_status(self, budget_type: str) -> str:
        """Return current budget status."""
        if budget_type not in self.budgets:
            return f"{budget_type}: untracked"
        spent = self.spent[budget_type]
        limit = self.budgets[budget_type]
        pct = (spent / limit * 100) if limit > 0 else 0
        return f"{budget_type}: {spent}/{limit} ({pct:.1f}%)"
    
    def reset(self, budget_type: str):
        """Reset spend counter for a budget type."""
        if budget_type in self.spent:
            self.spent[budget_type] = 0
            self.warnings_issued[budget_type] = False

# Singleton instance
_tracker = TokenBudgetTracker()

def track_budget(text: str, spend: int = 0) -> Optional[str]:
    """Parse budget from text, register if found, add spend, return warning."""
    parsed = _tracker.parse_budget(text)
    if parsed:
        _tracker.register_budget(*parsed)
    if spend > 0:
        return _tracker.add_spend(list(_tracker.budgets.keys())[0] if _tracker.budgets else "default", spend)
    return None