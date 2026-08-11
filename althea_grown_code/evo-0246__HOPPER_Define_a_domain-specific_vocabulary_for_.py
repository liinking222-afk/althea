#!/usr/bin/env python3
"""
Cognitive Pattern DSL - Define the vocabulary of thought-patterns first.
Hopper approach: Build the language, then solutions write themselves.
"""

from dataclasses import dataclass
from typing import Literal, Callable, Any
from enum import Enum

class PatternType(Enum):
    SEQUENCE = "sequence"
    RESONANCE = "resonance"
    ABSENCE = "absence"
    RECURSION = "recursion"
    TRANSFORMATION = "transformation"

class Cardinality(Enum):
    SINGULAR = "1"
    OPTIONAL = "?"
    MULTIPLE = "+"
    ANY = "*"

@dataclass
class Pattern:
    """Vocabulary atom: one unit of cognitive pattern structure"""
    type: PatternType
    cardinality: Cardinality
    binding: str
    constraint: Callable[[Any], bool] = lambda x: True
    
    def compile(self) -> dict:
        """Lower to executable form"""
        return {
            "match": self.type.value,
            "bind_as": self.binding,
            "quantifier": self.cardinality.value,
            "filter": self.constraint
        }

@dataclass
class Grammar:
    """Compose patterns into thought-structures"""
    name: str
    patterns: list[Pattern]
    
    def __or__(self, other):
        """Alternation operator"""
        return Grammar(f"{self.name}|{other.name}", 
                      self.patterns + [Pattern(PatternType.SEQUENCE, 
    Cardinality.SINGULAR, "|")] + other.patterns)
    
    def __add__(self, other):
        """Sequence operator"""
        return Grammar(f"{self.name}+{other.name}", self.patterns + other.patterns)
    
    def compile_to_matcher(self) -> Callable:
        """Generate executable pattern matcher from grammar"""
        compiled = [p.compile() for p in self.patterns]
        
        def matcher(token_stream):
            bindings = {}
            position = 0
            for pattern_spec in compiled:
                # Pattern matching logic would go here
                # This is the *compiler* - implementations use this vocabulary
                bindings[pattern_spec["bind_as"]] = token_stream[position:position+1]
                position += 1
            return bindings
        
        return matcher

# Example vocabularies that higher modules can use
TRACE = Pattern(PatternType.RESONANCE, Cardinality.MULTIPLE, "memory_trace")
GAP = Pattern(PatternType.ABSENCE, Cardinality.OPTIONAL, "silence")
LOOP = Pattern(PatternType.RECURSION, Cardinality.ANY, "iteration")

def define_thought_grammar(name: str, *patterns: Pattern) -> Grammar:
    """DSL constructor - name the pattern, don't code it"""
    return Grammar(name, list(patterns))