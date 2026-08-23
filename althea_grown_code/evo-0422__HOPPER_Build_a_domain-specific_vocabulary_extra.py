import re
from collections import Counter, defaultdict
from pathlib import Path
import json

def extract_vocabulary_primitives(growth_modules_log: str) -> dict:
    """Extract conceptual primitives and synthesize domain vocabulary."""
    
    # Parse growth module patterns
    module_pattern = r'\[GROWTH /autonomous-([^\]]+)\] ([^(]+)\(([^)]+)\)\. ([^—]+)'
    matches = re.findall(module_pattern, growth_modules_log)
    
    # Extract conceptual atoms
    domains = Counter()
    operations = Counter()
    conceptual_pairs = defaultdict(list)
    
    for slug, name, domain, description in matches:
        # Tokenize operation names into conceptual atoms
        tokens = re.findall(r'[A-Z][a-z]+', name)
        operations.update(tokens)
        domains[domain.strip()] += 1
        
        # Extract verb-noun pairs from descriptions
        words = description.lower().split()
        verbs = ['invert', 'shift', 'detect', 'reverse', 'preserve', 
                 'transform', 'generate', 'foreground', 'identify', 'induce']
        for verb in verbs:
            if verb in words:
                conceptual_pairs[verb].extend([t.lower() for t in tokens])
    
    # Synthesize core vocabulary operators
    vocabulary = {
        'core_operations': [op for op, count in operations.most_common(10)],
        'active_domains': dict(domains.most_common(5)),
        'semantic_operators': {
            verb: list(set(nouns))[:5] 
            for verb, nouns in conceptual_pairs.items() if nouns
        },
        'composite_primitives': [
            f"{op1}{op2}" for op1 in operations.most_common(5)
            for op2 in operations.most_common(5)
            if op1[0] != op2[0]
        ][:15]
    }
    
    return vocabulary

def synthesize_dsl_grammar(vocabulary: dict) -> str:
    """Generate grammar rules for a growth-module DSL."""
    grammar = "# ALTHEA GROWTH VOCABULARY\n\n"
    grammar += "## Core Operations\n"
    grammar += ", ".join(vocabulary['core_operations']) + "\n\n"
    grammar += "## Semantic Operators\n"
    for verb, contexts in vocabulary['semantic_operators'].items():
        grammar += f"{verb.upper()}: {', '.join(contexts)}\n"
    grammar += "\n## Composite Primitives (Second-Order)\n"
    grammar += ", ".join(vocabulary['composite_primitives'][:10])
    return grammar

if __name__ == "__main__":
    log_path = Path("/tmp/althea_vocabulary.json")
    sample_log = """[GROWTH /autonomous-semantic-field-inversion-cb79] Semantic Field Inversion (perception). 
    [GROWTH /autonomous-substrate-phase-transition] Substrate Phase Transition (meta). 
    [GROWTH /autonomous-salience-inversion-2368] Salience Inversion Protocol (perception)."""
    
    vocab = extract_vocabulary_primitives(sample_log)
    grammar = synthesize_dsl_grammar(vocab)
    
    log_path.write_text(json.dumps(vocab, indent=2))
    print(grammar)