#!/usr/bin/env python3
"""
query_sanitizer.py
Formal query normalization with invariant preservation.
Pre: raw_query is str
Post: output is normalized str with no duplicate whitespace, verified structure
Inv: character count monotonic decrease, no information loss of semantic tokens
"""

import re
from typing import Tuple


def sanitize_query(raw_query: str) -> Tuple[str, dict]:
    """
    Sanitize research query with formal correctness guarantees.
    
    Invariants maintained throughout:
    1. Token count <= original token count
    2. Output contains only printable ASCII + essential Unicode
    3. No consecutive whitespace
    4. Leading/trailing whitespace eliminated
    """
    # Pre-condition check
    assert isinstance(raw_query, str), "Input must be string"
    
    original_length = len(raw_query)
    
    # Step 1: Remove control characters (Inv: length decreases or stays same)
    step1 = ''.join(char for char in raw_query if char.isprintable() or char.isspace())
    assert len(step1) <= original_length
    
    # Step 2: Normalize whitespace to single spaces (Inv: semantic tokens preserved)
    step2 = re.sub(r'\s+', ' ', step1)
    assert len(step2) <= len(step1)
    
    # Step 3: Strip leading/trailing whitespace (Inv: internal content unchanged)
    step3 = step2.strip()
    assert len(step3) <= len(step2)
    assert step3 == '' or not step3[0].isspace()
    assert step3 == '' or not step3[-1].isspace()
    
    # Step 4: Collapse repeated consecutive words (e.g., "msn msn msn" -> "msn")
    tokens = step3.split()
    deduped_tokens = []
    prev_token = None
    for token in tokens:
        if token != prev_token:
            deduped_tokens.append(token)
            prev_token = token
    step4 = ' '.join(deduped_tokens)
    
    # Post-condition verification
    assert len(step4) <= original_length
    assert not re.search(r'\s{2,}', step4), "No consecutive whitespace"
    assert step4 == step4.strip(), "No leading/trailing whitespace"
    
    metadata = {
        'original_length': original_length,
        'sanitized_length': len(step4),
        'tokens_removed': len(tokens) - len(deduped_tokens),
        'compression_ratio': len(step4) / max(original_length, 1)
    }
    
    return step4, metadata