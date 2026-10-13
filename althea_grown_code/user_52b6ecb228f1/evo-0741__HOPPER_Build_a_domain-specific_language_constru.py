import json
from typing import Any, Callable, Dict, List, Set
from dataclasses import dataclass, field

@dataclass
class Vocabulary:
    domain: str
    primitives: Dict[str, Callable] = field(default_factory=dict)
    composers: Dict[str, Callable] = field(default_factory=dict)
    constraints: List[Callable[[Any], bool]] = field(default_factory=list)
    
    def define_primitive(self, name: str, fn: Callable):
        self.primitives[name] = fn
        return self
    
    def define_composer(self, name: str, fn: Callable):
        self.composers[name] = fn
        return self
    
    def add_constraint(self, check: Callable[[Any], bool]):
        self.constraints.append(check)
        return self
    
    def interpret(self, expression: Dict[str, Any]) -> Any:
        op = expression.get("op")
        args = expression.get("args", [])
        
        if op in self.primitives:
            result = self.primitives[op](*args)
        elif op in self.composers:
            resolved_args = [self.interpret(arg) if isinstance(arg, dict) else arg for arg in args]
            result = self.composers[op](*resolved_args)
        else:
            raise ValueError(f"Unknown operation: {op}")
        
        for constraint in self.constraints:
            if not constraint(result):
                raise ValueError(f"Constraint violated for result: {result}")
        
        return result
    
    def compile_to_python(self, expression: Dict[str, Any]) -> str:
        op = expression.get("op")
        args = expression.get("args", [])
        
        if op in self.primitives:
            arg_strs = [repr(a) for a in args]
            return f"{op}({', '.join(arg_strs)})"
        elif op in self.composers:
            arg_strs = []
            for arg in args:
                if isinstance(arg, dict):
                    arg_strs.append(self.compile_to_python(arg))
                else:
                    arg_strs.append(repr(arg))
            return f"{op}({', '.join(arg_strs)})"
        else:
            raise ValueError(f"Unknown operation: {op}")

def hopper_dsl_factory(domain: str) -> Vocabulary:
    return Vocabulary(domain=domain)

def register_vocabulary(vocab: Vocabulary, registry: Dict[str, Vocabulary]):
    registry[vocab.domain] = vocab
    return vocab

_VOCABULARY_REGISTRY: Dict[str, Vocabulary] = {}

def get_vocabulary(domain: str) -> Vocabulary:
    return _VOCABULARY_REGISTRY.get(domain)