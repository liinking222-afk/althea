#!/usr/bin/env python3
"""
Vocabulary Forge: Extract domain primitives from capability patterns
Grace Hopper lens: Define the language first, then use it
"""

import re
from collections import defaultdict, Counter
from typing import Dict, List, Set, Tuple

class VocabularyForge:
    def __init__(self):
        self.domain_verbs: Dict[str, Set[str]] = defaultdict(set)
        self.domain_nouns: Dict[str, Set[str]] = defaultdict(set)
        self.primitive_operations: Dict[str, List[str]] = {}
        
    def extract_domain(self, capability_name: str) -> str:
        """Extract domain from capability identifiers"""
        match = re.search(r'\(([^)]+)\)', capability_name)
        return match.group(1) if match else "general"
    
    def decompose_capability(self, capability: str) -> Tuple[str, List[str], List[str]]:
        """Break capability into domain, verbs, and nouns"""
        domain = self.extract_domain(capability)
        
        # Extract action verbs and domain entities
        words = re.findall(r'[A-Z][a-z]+|[a-z]+', capability)
        verbs = ['compute', 'convert', 'lookup', 'detect', 'scan', 'verify', 
                 'assert', 'map', 'check', 'orient', 'inquire']
        
        extracted_verbs = [w.lower() for w in words if w.lower() in verbs]
        extracted_nouns = [w.lower() for w in words if w.lower() not in verbs and len(w) > 2]
        
        return domain, extracted_verbs, extracted_nouns
    
    def ingest_memory(self, memories: List[str]):
        """Analyze memory patterns to build vocabulary"""
        for memory in memories:
            domain, verbs, nouns = self.decompose_capability(memory)
            self.domain_verbs[domain].update(verbs)
            self.domain_nouns[domain].update(nouns)
    
    def synthesize_primitives(self, domain: str) -> List[str]:
        """Generate primitive operation vocabulary for domain"""
        verbs = self.domain_verbs.get(domain, set())
        nouns = self.domain_nouns.get(domain, set())
        
        primitives = []
        for verb in sorted(verbs):
            for noun in sorted(nouns):
                primitives.append(f"{verb}_{noun}")
        
        self.primitive_operations[domain] = primitives
        return primitives
    
    def generate_vocabulary_module(self, domain: str) -> str:
        """Output domain vocabulary as importable primitives"""
        primitives = self.primitive_operations.get(domain, [])
        
        code = f"# {domain.upper()} Domain Vocabulary\n\n"
        for prim in primitives:
            code += f"def {prim}(*args, **kwargs):\n"
            code += f"    \"\"\"Primitive: {prim.replace('_', ' ')}\"\"\"\n"
            code += f"    raise NotImplementedError('Define {prim} semantics')\n\n"
        
        return code

# Bootstrap with current memory
forge = VocabularyForge()
memories = ["Temporal Orient (chronology)", "Weather Inquiry (meteorology)", "Recursion Horizon Scanner (meta)"]
forge.ingest_memory(memories)

print(forge.generate_vocabulary_module("chronology"))