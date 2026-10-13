import re
from typing import List, Dict, Tuple
from dataclasses import dataclass

@dataclass
class FragmentIntegrityReport:
    total_fragments: int
    truncated_count: int
    truncated_ids: List[str]
    integrity_score: float

class MemoryFragmentIntegrity:
    """Detects incomplete memory traces and computes integrity metrics."""
    
    TRUNCATION_PATTERNS = [
        r'—\s*rationale:\s*\w{0,20}$',  # Rationale cut mid-word
        r'\s+[A-Z][a-z]{0,5}$',  # Sentence cut early
        r'^.*\w{15,}$',  # Suspiciously ends in long partial word
        r'—.*[a-z]{1,3}$',  # Dash followed by fragment
    ]
    
    MIN_COMPLETE_LENGTH = 40
    
    def __init__(self):
        self.compiled_patterns = [re.compile(p) for p in self.TRUNCATION_PATTERNS]
    
    def is_truncated(self, fragment: str) -> Tuple[bool, str]:
        """Check if memory fragment appears incomplete."""
        stripped = fragment.strip()
        
        if len(stripped) < self.MIN_COMPLETE_LENGTH:
            return (True, "too_short")
        
        for pattern in self.compiled_patterns:
            if pattern.search(stripped):
                return (True, "pattern_match")
        
        if not any(stripped.endswith(term) for term in ['.', ')', ']', '}', '"']):
            if len(stripped) > 60:
                return (True, "no_terminal")
        
        return (False, "ok")
    
    def scan_memory_log(self, memory_entries: List[Dict[str, str]]) -> FragmentIntegrityReport:
        """Scan memory log and report integrity status."""
        truncated_ids = []
        
        for entry in memory_entries:
            content = entry.get('content', '')
            entry_id = entry.get('id', f"entry_{hash(content) % 10000}")
            
            is_trunc, reason = self.is_truncated(content)
            if is_trunc:
                truncated_ids.append(f"{entry_id}:{reason}")
        
        total = len(memory_entries)
        truncated = len(truncated_ids)
        score = 1.0 - (truncated / total) if total > 0 else 1.0
        
        return FragmentIntegrityReport(
            total_fragments=total,
            truncated_count=truncated,
            truncated_ids=truncated_ids,
            integrity_score=score
        )