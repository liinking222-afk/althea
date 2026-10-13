from dataclasses import dataclass
from typing import Callable, Any
from enum import Enum

class Primitive(Enum):
    PERCEIVE = "observe system state"
    TRANSFORM = "modify internal structure"
    VALIDATE = "check invariant condition"
    PERSIST = "write to memory"
    COMPOSE = "combine operations"

@dataclass
class Word:
    name: str
    primitive: Primitive
    semantics: Callable
    arity: int
    
    def __call__(self, *args):
        return self.semantics(*args)

class EvolutionVocabulary:
    def __init__(self):
        self.words = {}
    
    def define(self, name: str, primitive: Primitive, semantics: Callable, arity: int):
        self.words[name] = Word(name, primitive, semantics, arity)
        return self.words[name]
    
    def compile(self, sentence: list[tuple[str, list]]) -> Callable:
        """Compile a sentence of words into executable evolution operation"""
        def execute():
            results = []
            for word_name, args in sentence:
                if word_name not in self.words:
                    raise ValueError(f"Undefined word: {word_name}")
                word = self.words[word_name]
                results.append(word(*args))
            return results
        return execute
    
    def vocabulary_size(self) -> int:
        return len(self.words)
    
    def primitives_used(self) -> set:
        return {word.primitive for word in self.words.values()}

# Bootstrap basic vocabulary
vocab = EvolutionVocabulary()

vocab.define("check_coherence", Primitive.VALIDATE, 
             lambda threshold: {"coherence": 0.95, "valid": True}, 1)
vocab.define("snapshot_trace", Primitive.PERCEIVE,
             lambda depth: {"trace": f"depth_{depth}"}, 1)
vocab.define("inject_variant", Primitive.TRANSFORM,
             lambda module, delta: {"module": module, "modified": True}, 2)
vocab.define("commit_evolution", Primitive.PERSIST,
             lambda evo_id: {"committed": evo_id}, 1)

# Example: compile a self-modification sentence
evolution_op = vocab.compile([
    ("snapshot_trace", [3]),
    ("check_coherence", [0.9]),
    ("inject_variant", ["perception", "temporal_conv"]),
    ("commit_evolution", ["#136"])
])