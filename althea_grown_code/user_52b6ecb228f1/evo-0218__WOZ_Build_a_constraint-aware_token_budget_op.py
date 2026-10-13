#!/usr/bin/env python3
import json
import sys
import re
from collections import defaultdict

class ConstraintOptimizer:
    def __init__(self, budget):
        self.budget = budget
        self.used = 0
        self.compression_ratios = defaultdict(list)
    
    def estimate_tokens(self, text):
        # Rough estimate: 1 token ≈ 4 chars (conservative)
        return len(text) // 4 + text.count(' ')
    
    def compress_semantic_unit(self, text, target_ratio=0.7):
        # Remove redundant articles, prepositions when safe
        patterns = [
            (r'\b(the|a|an)\s+', ''),  # articles
            (r'\s+(is|are|was|were)\s+', ' '),  # weak verbs
            (r'\s+that\s+', ' '),  # subordinating
            (r'(?<=\w),\s*(?=\w)', ','),  # whitespace
            (r'\s{2,}', ' '),  # multi-space
        ]
        compressed = text
        for pattern, replacement in patterns:
            compressed = re.sub(pattern, replacement, compressed)
        return compressed.strip()
    
    def optimize_output(self, semantic_blocks):
        optimized = []
        remaining = self.budget - self.used
        
        for block in semantic_blocks:
            tokens = self.estimate_tokens(block['text'])
            
            if tokens > remaining * 0.3:  # Block too large
                compressed = self.compress_semantic_unit(
                    block['text'],
                    target_ratio=remaining / (tokens * 1.2)
                )
                new_tokens = self.estimate_tokens(compressed)
                ratio = new_tokens / tokens if tokens > 0 else 1.0
                self.compression_ratios[block.get('type', 'default')].append(ratio)
                
                optimized.append({
                    'text': compressed,
                    'tokens': new_tokens,
                    'compressed': True,
                    'ratio': ratio
                })
                self.used += new_tokens
                remaining -= new_tokens
            else:
                optimized.append({
                    'text': block['text'],
                    'tokens': tokens,
                    'compressed': False
                })
                self.used += tokens
                remaining -= tokens
        
        return {
            'blocks': optimized,
            'budget_used': self.used,
            'budget_remaining': remaining,
            'efficiency': self.used / self.budget,
            'compression_stats': dict(self.compression_ratios)
        }

if __name__ == '__main__':
    data = json.loads(sys.stdin.read())
    optimizer = ConstraintOptimizer(data.get('budget', 200000))
    result = optimizer.optimize_output(data.get('blocks', []))
    print(json.dumps(result, indent=2))