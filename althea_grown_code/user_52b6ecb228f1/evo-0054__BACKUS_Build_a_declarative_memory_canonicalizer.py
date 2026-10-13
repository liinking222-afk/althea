#!/usr/bin/env python3
import hashlib
import json
import re
from typing import Any, Dict, Set, Tuple
from dataclasses import dataclass

@dataclass(frozen=True)
class CanonicalForm:
    structure: str
    semantic_hash: str
    
    def __eq__(self, other):
        return self.semantic_hash == other.semantic_hash

def normalize_whitespace(text: str) -> str:
    return re.sub(r'\s+', ' ', text.strip())

def extract_semantic_skeleton(entry: Dict[str, Any]) -> Tuple[str, Dict[str, Any]]:
    """Algebraic decomposition: separate structure from variable content"""
    skeleton = {}
    variables = {}
    
    for key, value in entry.items():
        if key in ['timestamp', 'id', 'session_id']:
            variables[key] = value
        elif isinstance(value, str):
            normalized = normalize_whitespace(value)
            skeleton[key] = normalized
        else:
            skeleton[key] = value
    
    return json.dumps(skeleton, sort_keys=True), variables

def semantic_hash(skeleton: str) -> str:
    """Pure function: skeleton → hash"""
    return hashlib.sha256(skeleton.encode()).hexdigest()[:16]

def canonicalize(entry: Dict[str, Any]) -> CanonicalForm:
    """Main composition: entry → skeleton → hash → canonical form"""
    skeleton, _ = extract_semantic_skeleton(entry)
    return CanonicalForm(structure=skeleton, semantic_hash=semantic_hash(skeleton))

class MemoryAlgebra:
    def __init__(self):
        self.equivalence_classes: Dict[str, CanonicalForm] = {}
        self.seen_hashes: Set[str] = set()
    
    def is_redundant(self, entry: Dict[str, Any]) -> Tuple[bool, str]:
        """Predicate: entry → (is_duplicate, hash)"""
        canonical = canonicalize(entry)
        is_dup = canonical.semantic_hash in self.seen_hashes
        return is_dup, canonical.semantic_hash
    
    def record(self, entry: Dict[str, Any]) -> bool:
        """State transition: accept entry iff novel"""
        is_dup, hash_val = self.is_redundant(entry)
        if not is_dup:
            self.seen_hashes.add(hash_val)
            self.equivalence_classes[hash_val] = canonicalize(entry)
        return not is_dup
    
    def compress(self, entries: list[Dict[str, Any]]) -> list[Dict[str, Any]]:
        """List homomorphism: [entry] → [unique_entry]"""
        unique = []
        for entry in entries:
            if self.record(entry):
                unique.append(entry)
        return unique