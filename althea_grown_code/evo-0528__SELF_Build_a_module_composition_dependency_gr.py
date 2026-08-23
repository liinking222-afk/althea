import re
from collections import defaultdict, deque
from typing import Dict, List, Set, Tuple

def analyze_module_composition_opportunities(
    recent_modules: List[Dict],
    intent_similarity_threshold: float = 0.4
) -> Dict:
    """
    Analyzes recent module creations to detect composability opportunities.
    Returns potential composition patterns where new modules could be built
    from existing primitives rather than from scratch.
    """
    
    def tokenize_intent(intent: str) -> Set[str]:
        """Extract semantic tokens from module intent/description."""
        tokens = re.findall(r'\b[a-z]{3,}\b', intent.lower())
        stopwords = {'the', 'and', 'for', 'from', 'with', 'that', 'this'}
        return set(t for t in tokens if t not in stopwords)
    
    def compute_overlap(tokens1: Set[str], tokens2: Set[str]) -> float:
        """Jaccard similarity between token sets."""
        if not tokens1 or not tokens2:
            return 0.0
        return len(tokens1 & tokens2) / len(tokens1 | tokens2)
    
    # Build module knowledge graph
    modules = {}
    for mod in recent_modules:
        name = mod.get('name', mod.get('id', ''))
        intent = mod.get('intent', mod.get('description', ''))
        modules[name] = {
            'intent': intent,
            'tokens': tokenize_intent(intent),
            'dependencies': []
        }
    
    # Detect composition opportunities
    composition_graph = defaultdict(list)
    missed_opportunities = []
    
    for mod_name, mod_data in modules.items():
        for other_name, other_data in modules.items():
            if mod_name == other_name:
                continue
            
            overlap = compute_overlap(mod_data['tokens'], other_data['tokens'])
            
            if overlap > intent_similarity_threshold:
                composition_graph[mod_name].append({
                    'primitive': other_name,
                    'overlap': overlap,
                    'shared_concepts': list(mod_data['tokens'] & other_data['tokens'])
                })
    
    # Identify modules that could have been compositions
    for mod_name, primitives in composition_graph.items():
        if len(primitives) >= 2:
            missed_opportunities.append({
                'composite': mod_name,
                'could_use': [p['primitive'] for p in primitives],
                'rationale': f"Shares concepts with {len(primitives)} modules"
            })
    
    return {
        'composition_graph': dict(composition_graph),
        'missed_opportunities': missed_opportunities,
        'primitives_count': len(modules),
        'edges_count': sum(len(v) for v in composition_graph.values())
    }