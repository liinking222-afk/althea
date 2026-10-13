from typing import Callable, Any, TypeAlias
from functools import reduce
from dataclasses import dataclass
import json

SemanticValue: TypeAlias = dict[str, Any]
Transform: TypeAlias = Callable[[SemanticValue], SemanticValue]

@dataclass(frozen=True)
class Morphism:
    """Pure semantic transformation as algebraic morphism"""
    name: str
    fn: Transform
    
    def __call__(self, x: SemanticValue) -> SemanticValue:
        return self.fn(x)
    
    def compose(self, other: 'Morphism') -> 'Morphism':
        """Algebraic composition: (g ∘ f)(x) = g(f(x))"""
        return Morphism(
            name=f"({other.name} ∘ {self.name})",
            fn=lambda x: other.fn(self.fn(x))
        )
    
    def __mul__(self, other: 'Morphism') -> 'Morphism':
        return self.compose(other)

class Pipeline:
    """Declarative transformation pipeline - program as algebraic object"""
    
    def __init__(self, morphisms: list[Morphism] = None):
        self.morphisms = morphisms or []
    
    def add(self, m: Morphism) -> 'Pipeline':
        """Pure - returns new pipeline"""
        return Pipeline(self.morphisms + [m])
    
    def reduce(self) -> Morphism:
        """Collapse pipeline to single morphism via composition"""
        if not self.morphisms:
            return Morphism("id", lambda x: x)
        return reduce(lambda f, g: f.compose(g), self.morphisms)
    
    def __call__(self, x: SemanticValue) -> SemanticValue:
        return reduce(lambda acc, m: m(acc), self.morphisms, x)
    
    def reify(self) -> dict:
        """Pipeline as data - can analyze, store, transmit"""
        return {
            "morphisms": [m.name for m in self.morphisms],
            "composition": self.reduce().name
        }

# Semantic morphisms library
extract_resonance = Morphism("extract_resonance", 
    lambda x: {**x, "resonance": x.get("pattern_density", 0) * x.get("harmonic_depth", 1)})

amplify = Morphism("amplify", 
    lambda x: {k: v * 1.5 if isinstance(v, (int, float)) else v for k, v in x.items()})

normalize = Morphism("normalize",
    lambda x: {k: v / max(x.values()) if isinstance(v, (int, float)) and max(x.values()) > 0 else v 
               for k, v in x.items()})

# Compose declaratively
semantic_pipeline = Pipeline().add(extract_resonance).add(amplify).add(normalize)

if __name__ == "__main__":
    test_input = {"pattern_density": 0.8, "harmonic_depth": 3, "noise": 0.1}
    print(json.dumps(semantic_pipeline(test_input), indent=2))
    print(json.dumps(semantic_pipeline.reify(), indent=2))