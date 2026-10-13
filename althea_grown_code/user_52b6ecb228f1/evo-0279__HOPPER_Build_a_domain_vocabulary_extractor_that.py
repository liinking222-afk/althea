#!/usr/bin/env python3
import re
from dataclasses import dataclass
from typing import List, Dict, Set

@dataclass
class VocabTerm:
    term: str
    context: str
    frequency: int
    is_action: bool
    is_entity: bool

class VocabularyForge:
    """Grace Hopper lens: Extract domain vocabulary before solving"""
    
    def __init__(self):
        self.action_patterns = r'\b(design|build|create|analyze|detect|verify|validate|extract|route|bond|prevent)\w*\b'
        self.entity_patterns = r'\b([A-Z][a-z]+(?:[A-Z][a-z]+)*|(?:micro)?channel|layer|chassis|die|loop|state|pattern)\b'
        
    def extract_vocabulary(self, problem_text: str) -> Dict[str, VocabTerm]:
        """Extract the problem's native vocabulary"""
        vocab = {}
        words = problem_text.lower().split()
        
        # Extract actions (verbs/operations)
        for match in re.finditer(self.action_patterns, problem_text, re.IGNORECASE):
            term = match.group(0).lower()
            vocab[term] = VocabTerm(
                term=term,
                context=self._get_context(problem_text, match.start()),
                frequency=problem_text.lower().count(term),
                is_action=True,
                is_entity=False
            )
        
        # Extract entities (nouns/components)
        for match in re.finditer(self.entity_patterns, problem_text):
            term = match.group(0)
            key = term.lower()
            if key not in vocab:
                vocab[key] = VocabTerm(
                    term=term,
                    context=self._get_context(problem_text, match.start()),
                    frequency=problem_text.lower().count(key),
                    is_action=False,
                    is_entity=True
                )
        
        return vocab
    
    def _get_context(self, text: str, pos: int, window: int = 30) -> str:
        start = max(0, pos - window)
        end = min(len(text), pos + window)
        return text[start:end].strip()
    
    def generate_dsl_primitives(self, vocab: Dict[str, VocabTerm]) -> str:
        """Generate DSL primitive definitions from vocabulary"""
        dsl = "# DOMAIN-SPECIFIC LANGUAGE PRIMITIVES\n\n"
        
        actions = [v for v in vocab.values() if v.is_action and v.frequency > 0]
        entities = [v for v in vocab.values() if v.is_entity and v.frequency > 0]
        
        dsl += "# Actions (verbs)\n"
        for action in sorted(actions, key=lambda x: -x.frequency):
            dsl += f"def {action.term}(target, **params): pass  # {action.context[:40]}\n"
        
        dsl += "\n# Entities (nouns)\n"
        for entity in sorted(entities, key=lambda x: -x.frequency):
            dsl += f"class {entity.term.title().replace(' ', '')}:\n    pass  # {entity.context[:40]}\n"
        
        return dsl

if __name__ == "__main__":
    forge = VocabularyForge()
    problem = "Design a blueprint of liquid cooled phone with microchannel copper plate bonded to CPU die"
    vocab = forge.extract_vocabulary(problem)
    print(forge.generate_dsl_primitives(vocab))