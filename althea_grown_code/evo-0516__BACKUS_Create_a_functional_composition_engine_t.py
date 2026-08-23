from typing import Callable, TypeVar, Generic, Any
from dataclasses import dataclass
from functools import reduce

A = TypeVar('A')
B = TypeVar('B')
C = TypeVar('C')

@dataclass(frozen=True)
class Arrow(Generic[A, B]):
    """Pure function wrapper with explicit type contract"""
    fn: Callable[[A], B]
    input_contract: str
    output_contract: str
    
    def __call__(self, x: A) -> B:
        return self.fn(x)
    
    def compose(self, other: 'Arrow[B, C]') -> 'Arrow[A, C]':
        """Algebraic composition: g ∘ f"""
        return Arrow(
            fn=lambda x: other.fn(self.fn(x)),
            input_contract=self.input_contract,
            output_contract=other.output_contract
        )
    
    def __rshift__(self, other: 'Arrow') -> 'Arrow':
        """Pipeline operator: f >> g"""
        return self.compose(other)

class CompositionEngine:
    """Declarative module composition via functional algebra"""
    
    def __init__(self):
        self.registry: dict[str, Arrow] = {}
    
    def register(self, name: str, arrow: Arrow) -> None:
        self.registry[name] = arrow
    
    def pipeline(self, *names: str) -> Arrow:
        """Compose registered arrows left-to-right"""
        arrows = [self.registry[n] for n in names]
        return reduce(lambda f, g: f >> g, arrows)
    
    def contract_chain(self, *names: str) -> str:
        """Derive algebraic proof of composition validity"""
        arrows = [self.registry[n] for n in names]
        contracts = [f"{a.input_contract} → {a.output_contract}" for a in arrows]
        return " ∘ ".join(contracts)
    
    def verify(self, *names: str) -> bool:
        """Check if arrows compose (output matches next input)"""
        arrows = [self.registry[n] for n in names]
        for i in range(len(arrows) - 1):
            if arrows[i].output_contract != arrows[i + 1].input_contract:
                return False
        return True

engine = CompositionEngine()

parse_request = Arrow(lambda x: x.lower().strip(), "RawText", "NormalizedText")
extract_intent = Arrow(lambda x: x.split()[0] if x else "", "NormalizedText", "Intent")
route_handler = Arrow(lambda x: f"handler_{x}", "Intent", "ModulePath")

engine.register("parse", parse_request)
engine.register("extract", extract_intent)
engine.register("route", route_handler)

composed = engine.pipeline("parse", "extract", "route")
proof = engine.contract_chain("parse", "extract", "route")