#!/usr/bin/env python3
"""
vocabulary_first.py — Hopper-inspired DSL constructor
Build the language of the problem, then solve in that language.
"""

from typing import Dict, List, Callable, Any
from dataclasses import dataclass
import json


@dataclass
class Primitive:
    name: str
    fn: Callable
    signature: str


class VocabularySpace:
    def __init__(self, domain: str):
        self.domain = domain
        self.primitives: Dict[str, Primitive] = {}
        self.combinators: Dict[str, Callable] = {}
        self.compiled_solutions: List[str] = []
    
    def define_primitive(self, name: str, fn: Callable, signature: str):
        """Define a word in the problem's vocabulary"""
        self.primitives[name] = Primitive(name, fn, signature)
        return self
    
    def define_combinator(self, name: str, combinator: Callable):
        """Define how primitives compose"""
        self.combinators[name] = combinator
        return self
    
    def express(self, solution_expr: str) -> Any:
        """Write solution in the defined vocabulary"""
        self.compiled_solutions.append(solution_expr)
        return eval(solution_expr, {
            **{p.name: p.fn for p in self.primitives.values()},
            **self.combinators
        })
    
    def vocabulary_spec(self) -> Dict:
        """Export the vocabulary for reuse/extension"""
        return {
            "domain": self.domain,
            "primitives": {
                name: p.signature for name, p in self.primitives.items()
            },
            "combinators": list(self.combinators.keys()),
            "solutions_written": len(self.compiled_solutions)
        }


def create_vocabulary(domain: str) -> VocabularySpace:
    """Factory: start by naming the problem space"""
    return VocabularySpace(domain)


# Self-test: metric calculation vocabulary
if __name__ == "__main__":
    metrics_lang = create_vocabulary("integrity_metrics")
    
    metrics_lang.define_primitive("sample", lambda x: x[:100], "List[T] -> List[T]")
    metrics_lang.define_primitive("variance", lambda x: sum((i-sum(x)/len(x))**2 for i in x)/len(x), "List[Float] -> Float")
    metrics_lang.define_primitive("normalize", lambda x: [i/max(x) for i in x], "List[Float] -> List[Float]")
    metrics_lang.define_combinator("pipe", lambda f, g: lambda x: g(f(x)))
    
    result = metrics_lang.express("normalize(sample([1,2,3,4,5]*20))")
    print(json.dumps(metrics_lang.vocabulary_spec(), indent=2))