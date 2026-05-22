#!/usr/bin/env python3
"""DSL Constructor - Hopper Archetype Module
Generates problem-specific vocabularies from constraint topology analysis."""

from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Set
import inspect
import re

@dataclass
class Vocabulary:
    """A problem-specific language element."""
    name: str
    constraint_pattern: str
    impl: Callable
    dependencies: Set[str]

class DSLConstructor:
    def __init__(self):
        self.vocabularies: Dict[str, Vocabulary] = {}
        self.constraint_graph: Dict[str, Set[str]] = {}
    
    def extract_constraints(self, problem_description: str) -> List[str]:
        """Extract constraint patterns from natural language or code."""
        patterns = []
        # Detect recurring structural patterns
        for line in problem_description.split('\n'):
            if any(kw in line.lower() for kw in ['must', 'requires', 'ensures', 'invariant', 'when', 'if']):
                patterns.append(line.strip())
        return patterns
    
    def define_word(self, name: str, constraint: str, implementation: Callable) -> None:
        """Add a vocabulary word with its constraint pattern and implementation."""
        sig = inspect.signature(implementation)
        deps = set(sig.parameters.keys())
        
        vocab = Vocabulary(name, constraint, implementation, deps)
        self.vocabularies[name] = vocab
        self.constraint_graph[name] = deps
    
    def compile_solution(self, vocabulary_sequence: List[str]) -> Callable:
        """Compile a solution from vocabulary words in dependency order."""
        def solution(*args, **kwargs):
            context = kwargs.copy()
            for word in vocabulary_sequence:
                if word in self.vocabularies:
                    vocab = self.vocabularies[word]
                    word_args = {k: context[k] for k in vocab.dependencies if k in context}
                    result = vocab.impl(**word_args)
                    context[word] = result
            return context
        return solution
    
    def topological_sort(self, words: List[str]) -> List[str]:
        """Sort vocabulary words by constraint dependencies."""
        visited = set()
        order = []
        
        def visit(word: str):
            if word in visited or word not in self.constraint_graph:
                return
            visited.add(word)
            for dep in self.constraint_graph[word]:
                visit(dep)
            order.append(word)
        
        for word in words:
            visit(word)
        return order
    
    def vocabulary_size(self) -> int:
        return len(self.vocabularies)