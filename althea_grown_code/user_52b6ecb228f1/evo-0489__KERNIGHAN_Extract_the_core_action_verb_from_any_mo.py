import re
from typing import Optional

def extract_action_verb(name: str) -> Optional[str]:
    """Return the primary action verb from a module name or description."""
    name = name.lower().strip()
    
    # Remove common prefixes
    name = re.sub(r'^(autonomous[_-]?|auto[_-]?)', '', name)
    
    # Split on delimiters
    tokens = re.split(r'[_\-\s/]+', name)
    
    # Action verbs that indicate primary responsibility
    action_verbs = {
        'scan', 'detect', 'map', 'compute', 'render', 'visualize', 'analyze',
        'parse', 'extract', 'transform', 'filter', 'build', 'create', 'generate',
        'validate', 'check', 'verify', 'load', 'save', 'read', 'write',
        'fetch', 'query', 'search', 'find', 'sort', 'merge', 'split',
        'encode', 'decode', 'compress', 'decompress', 'hash', 'sign',
        'send', 'receive', 'connect', 'close', 'listen', 'serve'
    }
    
    # Find first action verb
    for token in tokens:
        if token in action_verbs:
            return token
    
    # Check for verb patterns (ends in common verb suffixes)
    for token in tokens:
        if re.match(r'^(.*)(ing|ize|ify|ate)$', token):
            return token
    
    return tokens[0] if tokens else None

def is_single_responsibility(description: str) -> bool:
    """Check if description suggests single responsibility (no 'and' conjunctions)."""
    desc_lower = description.lower()
    conjunctions = [' and ', ' or ', ' also ', ' plus ', ' with ']
    return not any(conj in desc_lower for conj in conjunctions)

def kernighan_check(name: str, description: str = "") -> dict:
    """Validate module adheres to Kernighan principles."""
    return {
        'action': extract_action_verb(name),
        'single_responsibility': is_single_responsibility(description) if description else None,
        'name_length': len(name.split()),
        'clear': len(name.split()) <= 4
    }