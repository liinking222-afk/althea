#!/usr/bin/env python3
"""Pattern Language Compiler - defines AUTOSYNTH trigger vocabulary and grammar"""

from dataclasses import dataclass
from typing import Dict, Set, Callable
import re

@dataclass
class PatternGrammar:
    """Defines the vocabulary of a pattern before it can trigger"""
    name: str
    required_tokens: Set[str]
    forbidden_contexts: Set[str]
    cooldown_turns: int
    validator: Callable[[str], bool]

class PatternLanguageCompiler:
    def __init__(self):
        self.vocabulary: Dict[str, PatternGrammar] = {}
        self.trigger_history: Dict[str, int] = {}
        self.current_turn = 0
        
    def define_pattern(self, grammar: PatternGrammar) -> None:
        """Define vocabulary before use - Hopper principle"""
        self.vocabulary[grammar.name] = grammar
        
    def compile_trigger(self, pattern_name: str, context: str) -> bool:
        """Compile trigger decision using defined vocabulary"""
        if pattern_name not in self.vocabulary:
            return False
            
        grammar = self.vocabulary[pattern_name]
        
        # Check cooldown using vocabulary
        last_trigger = self.trigger_history.get(pattern_name, -999)
        if self.current_turn - last_trigger < grammar.cooldown_turns:
            return False
            
        # Check required tokens
        context_lower = context.lower()
        if not any(token in context_lower for token in grammar.required_tokens):
            return False
            
        # Check forbidden contexts
        if any(forbidden in context_lower for forbidden in grammar.forbidden_contexts):
            return False
            
        # Apply custom validator from vocabulary
        if not grammar.validator(context):
            return False
            
        self.trigger_history[pattern_name] = self.current_turn
        return True
    
    def advance_turn(self) -> None:
        self.current_turn += 1

# Initialize with vocabulary definitions
compiler = PatternLanguageCompiler()

# Define linguistic-bridge vocabulary
compiler.define_pattern(PatternGrammar(
    name="linguistic-bridge",
    required_tokens={"translate", "language", "mean", "say"},
    forbidden_contexts={"already translated", "just translated"},
    cooldown_turns=5,
    validator=lambda ctx: len(ctx.split()) > 10
))

# Define market-inquiry vocabulary
compiler.define_pattern(PatternGrammar(
    name="market-inquiry",
    required_tokens={"price", "market", "stock", "quote"},
    forbidden_contexts={"historical", "past"},
    cooldown_turns=3,
    validator=lambda ctx: bool(re.search(r'\b[A-Z]{2,5}\b', ctx))
))