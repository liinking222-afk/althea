import json
from pathlib import Path
from typing import Dict, List, Any, Callable
from dataclasses import dataclass, asdict

@dataclass
class Primitive:
    name: str
    domain: str
    signature: str
    intent: str
    implementation: str = ""

@dataclass
class Vocabulary:
    domain: str
    primitives: Dict[str, Primitive]
    compositions: Dict[str, List[str]]

class VocabularyEngine:
    def __init__(self, vocab_dir: Path = Path("./vocabularies")):
        self.vocab_dir = vocab_dir
        self.vocab_dir.mkdir(exist_ok=True)
        self.vocabularies: Dict[str, Vocabulary] = {}
        self.load_all()
    
    def define_primitive(self, domain: str, name: str, signature: str, intent: str):
        if domain not in self.vocabularies:
            self.vocabularies[domain] = Vocabulary(domain, {}, {})
        prim = Primitive(name, domain, signature, intent)
        self.vocabularies[domain].primitives[name] = prim
        self.save_vocabulary(domain)
        return prim
    
    def compose(self, domain: str, pattern_name: str, primitive_sequence: List[str]):
        if domain not in self.vocabularies:
            raise ValueError(f"Domain {domain} not defined")
        self.vocabularies[domain].compositions[pattern_name] = primitive_sequence
        self.save_vocabulary(domain)
    
    def save_vocabulary(self, domain: str):
        vocab = self.vocabularies[domain]
        data = {
            "domain": vocab.domain,
            "primitives": {k: asdict(v) for k, v in vocab.primitives.items()},
            "compositions": vocab.compositions
        }
        path = self.vocab_dir / f"{domain}.vocab.json"
        path.write_text(json.dumps(data, indent=2))
    
    def load_all(self):
        for path in self.vocab_dir.glob("*.vocab.json"):
            data = json.loads(path.read_text())
            primitives = {k: Primitive(**v) for k, v in data["primitives"].items()}
            self.vocabularies[data["domain"]] = Vocabulary(
                data["domain"], primitives, data["compositions"]
            )
    
    def describe_domain(self, domain: str) -> str:
        if domain not in self.vocabularies:
            return f"Domain {domain} undefined"
        vocab = self.vocabularies[domain]
        lines = [f"DOMAIN: {domain}", "PRIMITIVES:"]
        for name, prim in vocab.primitives.items():
            lines.append(f"  {name}: {prim.signature} — {prim.intent}")
        lines.append("COMPOSITIONS:")
        for pattern, seq in vocab.compositions.items():
            lines.append(f"  {pattern} = {' → '.join(seq)}")
        return "\n".join(lines)

if __name__ == "__main__":
    engine = VocabularyEngine()
    engine.define_primitive("fractal", "iterate", "fn(z, c) -> z", "Apply fractal iteration")
    engine.define_primitive("fractal", "divergence_test", "fn(z, threshold) -> bool", "Test escape condition")
    engine.compose("fractal", "mandelbrot_point", ["iterate", "divergence_test"])
    print(engine.describe_domain("fractal"))