from functools import reduce
from typing import Callable, List, Dict, Any, Tuple
from hashlib import sha256
import json

# Pure functions - no side effects, composable transformations

def normalize(memory: Dict[str, Any]) -> Dict[str, Any]:
    """Canonicalize memory structure for comparison."""
    return {
        'type': memory.get('type', ''),
        'pattern': memory.get('pattern', ''),
        'context': str(memory.get('context', '')).lower().strip()
    }

def hash_memory(memory: Dict[str, Any]) -> str:
    """Pure hash function - same input always yields same output."""
    canonical = json.dumps(normalize(memory), sort_keys=True)
    return sha256(canonical.encode()).hexdigest()[:16]

def similarity_score(m1: Dict[str, Any], m2: Dict[str, Any]) -> float:
    """Compute algebraic distance between memories [0,1]."""
    n1, n2 = normalize(m1), normalize(m2)
    matches = sum(1 for k in n1 if n1[k] == n2.get(k))
    return matches / len(n1) if n1 else 0.0

def cluster_predicate(threshold: float) -> Callable[[Dict, Dict], bool]:
    """Higher-order function returning a clustering predicate."""
    return lambda m1, m2: similarity_score(m1, m2) >= threshold

def partition_by(pred: Callable[[Any, Any], bool], items: List[Any]) -> List[List[Any]]:
    """Pure partition function - groups items by predicate."""
    clusters = []
    for item in items:
        placed = False
        for cluster in clusters:
            if pred(item, cluster[0]):
                cluster.append(item)
                placed = True
                break
        if not placed:
            clusters.append([item])
    return clusters

# Compose the pipeline as function composition
compose = lambda *fns: reduce(lambda f, g: lambda x: f(g(x)), fns, lambda x: x)

def deduplicate_memories(memories: List[Dict[str, Any]], threshold: float = 0.8) -> List[Dict[str, Any]]:
    """Declarative pipeline: partition → select representatives."""
    clusters = partition_by(cluster_predicate(threshold), memories)
    representatives = [cluster[0] for cluster in clusters]
    return representatives

# Export pure transformation
def compress(memory_stream: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], Dict[str, int]]:
    """Main algebraic compression: stream → (compressed_stream, metadata)."""
    compressed = deduplicate_memories(memory_stream)
    metadata = {
        'original': len(memory_stream),
        'compressed': len(compressed),
        'ratio': len(compressed) / len(memory_stream) if memory_stream else 1.0
    }
    return compressed, metadata