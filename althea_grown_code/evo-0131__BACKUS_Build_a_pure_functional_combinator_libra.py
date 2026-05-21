#!/usr/bin/env python3
from typing import Callable, TypeVar, Tuple, Any
from functools import reduce
import json

A = TypeVar('A')
B = TypeVar('B')
C = TypeVar('C')

class CognitiveF:
    """Functional combinators for reasoning about cognitive transformations"""
    
    @staticmethod
    def identity(x: A) -> A:
        """Identity morphism: id(x) = x"""
        return x
    
    @staticmethod
    def compose(g: Callable[[B], C], f: Callable[[A], B]) -> Callable[[A], C]:
        """Function composition: (g ∘ f)(x) = g(f(x))"""
        return lambda x: g(f(x))
    
    @staticmethod
    def verify_associativity(f, g, h, test_input) -> bool:
        """Verify (h ∘ g) ∘ f = h ∘ (g ∘ f)"""
        left = CognitiveF.compose(CognitiveF.compose(h, g), f)
        right = CognitiveF.compose(h, CognitiveF.compose(g, f))
        return left(test_input) == right(test_input)
    
    @staticmethod
    def verify_identity(f, test_input) -> bool:
        """Verify f ∘ id = id ∘ f = f"""
        left = CognitiveF.compose(f, CognitiveF.identity)(test_input)
        right = CognitiveF.compose(CognitiveF.identity, f)(test_input)
        return left == right == f(test_input)
    
    @staticmethod
    def curry(f: Callable) -> Callable:
        """Transform multi-arg function into chain of single-arg functions"""
        def curried(x):
            def inner(y):
                return f(x, y)
            return inner
        return curried
    
    @staticmethod
    def pipe(*functions) -> Callable:
        """Left-to-right composition: pipe(f,g,h)(x) = h(g(f(x)))"""
        return lambda x: reduce(lambda acc, f: f(acc), functions, x)
    
    @staticmethod
    def kleisli_compose(g: Callable[[B], Tuple[C, str]], 
                       f: Callable[[A], Tuple[B, str]]) -> Callable[[A], Tuple[C, str]]:
        """Monadic composition preserving cognitive trace"""
        def composed(x):
            b, trace1 = f(x)
            c, trace2 = g(b)
            return c, f"{trace1} >> {trace2}"
        return composed
    
    @staticmethod
    def algebraic_property_check(operation_name: str, f, g, h, test_inputs: list) -> dict:
        """Check algebraic properties across test cases"""
        results = {
            "operation": operation_name,
            "associative": all(CognitiveF.verify_associativity(f, g, h, x) for x in test_inputs),
            "identity_preserved": all(CognitiveF.verify_identity(f, x) for x in test_inputs),
            "test_count": len(test_inputs)
        }
        return results

if __name__ == "__main__":
    extract = lambda x: x.get("value", 0)
    double = lambda x: x * 2
    increment = lambda x: x + 1
    
    tests = [{"value": 5}, {"value": 10}, {"value": 0}]
    props = CognitiveF.algebraic_property_check("test_pipeline", extract, double, increment, tests)
    
    pipeline = CognitiveF.pipe(extract, double, increment)
    print(json.dumps({"algebraic_verification": props, "sample_result": pipeline({"value": 5})}))