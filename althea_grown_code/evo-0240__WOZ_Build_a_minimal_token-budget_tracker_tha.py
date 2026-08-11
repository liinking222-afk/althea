#!/usr/bin/env python3
"""Token Budget Enforcer - Wozniak constraint elegance"""
import sys
import json
from pathlib import Path

BUDGET_FILE = Path.home() / ".althea" / "token_budget.json"
BUDGET_FILE.parent.mkdir(exist_ok=True)

def load_budget():
    if BUDGET_FILE.exists():
        return json.loads(BUDGET_FILE.read_text())
    return {"allocated": 200000, "used": 0, "reserved": 0}

def save_budget(budget):
    BUDGET_FILE.write_text(json.dumps(budget, indent=2))

def estimate_tokens(text):
    """Rough estimate: 1 token ≈ 4 chars"""
    return len(text) // 4

def reserve(amount, tag=""):
    budget = load_budget()
    available = budget["allocated"] - budget["used"] - budget["reserved"]
    if amount > available:
        print(f"BUDGET_EXCEEDED: need {amount}, have {available}", file=sys.stderr)
        sys.exit(1)
    budget["reserved"] += amount
    save_budget(budget)
    return {"status": "reserved", "amount": amount, "remaining": available - amount}

def commit(amount):
    budget = load_budget()
    budget["used"] += amount
    budget["reserved"] = max(0, budget["reserved"] - amount)
    save_budget(budget)
    return {"status": "committed", "used": budget["used"], "allocated": budget["allocated"]}

def status():
    budget = load_budget()
    available = budget["allocated"] - budget["used"] - budget["reserved"]
    utilization = budget["used"] / budget["allocated"] if budget["allocated"] > 0 else 0
    return {**budget, "available": available, "utilization": f"{utilization:.1%}"}

if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "status"
    
    if cmd == "reserve":
        amount = int(sys.argv[2])
        tag = sys.argv[3] if len(sys.argv) > 3 else ""
        print(json.dumps(reserve(amount, tag)))
    elif cmd == "commit":
        amount = int(sys.argv[2])
        print(json.dumps(commit(amount)))
    elif cmd == "estimate":
        text = sys.stdin.read() if len(sys.argv) == 2 else sys.argv[2]
        print(json.dumps({"estimated_tokens": estimate_tokens(text)}))
    else:
        print(json.dumps(status()))