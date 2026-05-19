#!/usr/bin/env python3
"""Module Purpose Validator - ensures one-function-per-module discipline"""

import re
from collections import defaultdict
from typing import Dict, List, Tuple

class PurposeValidator:
    def __init__(self):
        self.verbs = defaultdict(list)  # verb -> [module_names]
        self.violations = []
        
    def extract_verbs(self, text: str) -> List[str]:
        """Extract action verbs from module description"""
        words = re.findall(r'\b[a-z]+\b', text.lower())
        action_verbs = [w for w in words if w in {
            'build', 'track', 'map', 'generate', 'sustain', 'treat',
            'eliminate', 'compile', 'validate', 'route', 'cache',
            'profile', 'compose', 'reassign', 'reveal', 'extract'
        }]
        return action_verbs
    
    def count_conjunctions(self, text: str) -> int:
        """Count coordinating conjunctions suggesting multiple purposes"""
        return len(re.findall(r'\b(and|or|plus|also|additionally)\b', text.lower()))
    
    def validate_module(self, name: str, description: str) -> Tuple[bool, str]:
        """Check if module does ONE thing"""
        verbs = self.extract_verbs(description)
        conj = self.count_conjunctions(description)
        
        if len(verbs) > 2 or conj > 1:
            reason = f"multiple_verbs={len(verbs)},conjunctions={conj}"
            self.violations.append((name, reason))
            return False, reason
        
        if verbs:
            for v in verbs:
                self.verbs[v].append(name)
        
        return True, "clear_single_purpose"
    
    def report(self) -> str:
        """Generate clarity report"""
        lines = ["=== MODULE CLARITY REPORT ==="]
        lines.append(f"Total violations: {len(self.violations)}")
        
        for name, reason in self.violations:
            lines.append(f"VIOLATES: {name} ({reason})")
        
        lines.append("\n=== VERB DISTRIBUTION ===")
        for verb in sorted(self.verbs.keys()):
            modules = self.verbs[verb]
            if len(modules) > 1:
                lines.append(f"{verb}: {len(modules)} modules (check overlap)")
        
        return "\n".join(lines)

def main():
    validator = PurposeValidator()
    
    # Self-test on recent memory
    test_cases = [
        ("hot-path-router", "route modules with flags"),
        ("composition-cache", "cache compositions and eliminate overhead"),
        ("paradox-stabilizer", "generate and sustain contradictory states"),
    ]
    
    for name, desc in test_cases:
        valid, reason = validator.validate_module(name, desc)
        print(f"{name}: {'✓' if valid else '✗'} ({reason})")
    
    print("\n" + validator.report())

if __name__ == "__main__":
    main()