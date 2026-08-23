#!/usr/bin/env python3
import sys
import re
from dataclasses import dataclass
from typing import Optional

@dataclass
class TokenProfile:
    module_id: str
    estimated_tokens: int
    budget_limit: int
    utilization: float

def count_tokens_rough(text: str) -> int:
    """Rough token estimate: ~4 chars per token average"""
    return len(text) // 4

def extract_budget(text: str) -> Optional[int]:
    """Extract budget from <budget:token_budget> tags"""
    match = re.search(r'<budget:token_budget>(\d+)</budget:token_budget>', text)
    return int(match.group(1)) if match else None

def extract_module_id(text: str) -> Optional[str]:
    """Extract module identifier from INTENT or filename"""
    intent_match = re.search(r'INTENT:\s*(.+)', text)
    if intent_match:
        intent = intent_match.group(1)
        words = re.findall(r'\b[a-z_]+\b', intent.lower())
        return '_'.join(words[:3]) if words else 'unknown'
    return 'unknown'

def profile_evolution_cycle(input_text: str) -> TokenProfile:
    """Profile a single evolution cycle's token usage"""
    token_count = count_tokens_rough(input_text)
    budget = extract_budget(input_text) or 200000
    module_id = extract_module_id(input_text)
    utilization = (token_count / budget) * 100
    
    return TokenProfile(
        module_id=module_id,
        estimated_tokens=token_count,
        budget_limit=budget,
        utilization=utilization
    )

def format_profile(profile: TokenProfile) -> str:
    """Output TSV-compatible profile line"""
    warn = "⚠️WARN" if profile.utilization > 75 else "OK"
    return f"{profile.module_id}\t{profile.estimated_tokens}\t{profile.budget_limit}\t{profile.utilization:.1f}%\t{warn}"

if __name__ == "__main__":
    input_text = sys.stdin.read()
    profile = profile_evolution_cycle(input_text)
    print(format_profile(profile))