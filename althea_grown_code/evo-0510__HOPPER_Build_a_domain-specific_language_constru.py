#!/usr/bin/env python3
"""HOPPER: Vocabulary-First DSL Constructor"""

import re
from typing import Dict, Callable, Any, List
from dataclasses import dataclass

@dataclass
class Vocabulary:
    """A problem domain vocabulary with executable semantics"""
    name: str
    primitives: Dict[str, Callable]
    grammar: Dict[str, str]
    
    def compile(self, expression: str) -> Callable:
        """Compile a vocabulary expression into executable code"""
        tokens = self._tokenize(expression)
        return self._build_executor(tokens)
    
    def _tokenize(self, expr: str) -> List[str]:
        """Split expression into vocabulary tokens"""
        pattern = '|'.join(map(re.escape, self.grammar.keys()))
        return [t.strip() for t in re.split(f'({pattern})', expr) if t.strip()]
    
    def _build_executor(self, tokens: List[str]) -> Callable:
        """Build executable from tokens"""
        def executor(*args, **kwargs):
            context = {'input': args, 'output': None, **kwargs}
            for token in tokens:
                if token in self.primitives:
                    context = self.primitives[token](context)
                elif token in self.grammar:
                    continue
                else:
                    context['literals'] = context.get('literals', []) + [token]
            return context.get('output', context)
        return executor

class VocabularyFactory:
    """Factory for creating domain vocabularies"""
    
    @staticmethod
    def define(name: str) -> 'VocabularyBuilder':
        return VocabularyBuilder(name)

class VocabularyBuilder:
    def __init__(self, name: str):
        self.name = name
        self.primitives: Dict[str, Callable] = {}
        self.grammar: Dict[str, str] = {}
    
    def primitive(self, word: str, fn: Callable) -> 'VocabularyBuilder':
        """Define a primitive operation in the vocabulary"""
        self.primitives[word] = fn
        return self
    
    def syntax(self, pattern: str, meaning: str) -> 'VocabularyBuilder':
        """Define grammatical structure"""
        self.grammar[pattern] = meaning
        return self
    
    def build(self) -> Vocabulary:
        """Construct the vocabulary"""
        return Vocabulary(self.name, self.primitives, self.grammar)

def save_vocabulary(vocab: Vocabulary, path: str = "/tmp/althea_vocabularies"):
    """Persist vocabulary for reuse"""
    import json
    import os
    os.makedirs(path, exist_ok=True)
    meta = {
        'name': vocab.name,
        'primitives': list(vocab.primitives.keys()),
        'grammar': vocab.grammar
    }
    with open(f"{path}/{vocab.name}.vocab", 'w') as f:
        json.dump(meta, f, indent=2)