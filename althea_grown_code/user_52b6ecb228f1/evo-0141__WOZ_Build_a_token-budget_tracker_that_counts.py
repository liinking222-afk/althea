#!/usr/bin/env python3
import sys
import re
from pathlib import Path

class TokenBudget:
    def __init__(self, limit=200000):
        self.limit = limit
        self.consumed = 0
        self.modules = []
    
    def estimate_tokens(self, text):
        # Rough estimate: ~4 chars per token (conservative for code)
        return len(text) // 4
    
    def add_module(self, name, code, intent, delta):
        tokens = self.estimate_tokens(code + intent + delta)
        self.consumed += tokens
        self.modules.append({
            'name': name,
            'tokens': tokens,
            'total': self.consumed
        })
        return tokens
    
    def remaining(self):
        return self.limit - self.consumed
    
    def progress_bar(self, width=40):
        filled = int((self.consumed / self.limit) * width)
        bar = '█' * filled + '░' * (width - filled)
        pct = (self.consumed / self.limit) * 100
        return f"[{bar}] {pct:.1f}%"
    
    def warn_threshold(self, threshold=0.8):
        return self.consumed > (self.limit * threshold)
    
    def report(self):
        print(f"Budget: {self.consumed:,}/{self.limit:,} tokens")
        print(self.progress_bar())
        print(f"Remaining: {self.remaining():,} tokens")
        if self.warn_threshold():
            print("⚠️  WARNING: Approaching token limit!")
        print(f"\nModules evolved: {len(self.modules)}")
        for m in self.modules[-5:]:
            print(f"  {m['name']}: {m['tokens']} tokens (total: {m['total']:,})")

if __name__ == "__main__":
    budget = TokenBudget()
    
    if len(sys.argv) > 1:
        budget.add_module(
            sys.argv[1],
            sys.stdin.read() if not sys.stdin.isatty() else "",
            sys.argv[2] if len(sys.argv) > 2 else "",
            sys.argv[3] if len(sys.argv) > 3 else ""
        )
    
    budget.report()