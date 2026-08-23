import hashlib
from collections import defaultdict
from dataclasses import dataclass
from typing import List, Tuple

@dataclass
class InputFragment:
    content: str
    hash: str
    timestamp: float

class RepetitionDetector:
    def __init__(self, window_size: int = 10, similarity_threshold: float = 0.85):
        self.window_size = window_size
        self.similarity_threshold = similarity_threshold
        self.recent_fragments: List[InputFragment] = []
        self.hash_counts = defaultdict(int)
        
    def compute_hash(self, text: str) -> str:
        normalized = ''.join(text.lower().split())
        return hashlib.sha256(normalized.encode()).hexdigest()[:16]
    
    def compute_similarity(self, text1: str, text2: str) -> float:
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())
        if not words1 or not words2:
            return 0.0
        intersection = len(words1 & words2)
        union = len(words1 | words2)
        return intersection / union if union > 0 else 0.0
    
    def detect(self, input_text: str, timestamp: float) -> Tuple[bool, str]:
        input_hash = self.compute_hash(input_text)
        
        # Exact duplicate detection
        if self.hash_counts[input_hash] > 0:
            self.hash_counts[input_hash] += 1
            return True, f"EXACT_DUPLICATE:{self.hash_counts[input_hash]}"
        
        # Semantic similarity detection
        for fragment in self.recent_fragments[-self.window_size:]:
            similarity = self.compute_similarity(input_text, fragment.content)
            if similarity >= self.similarity_threshold:
                return True, f"SEMANTIC_DUPLICATE:{similarity:.2f}"
        
        # Store fragment
        self.recent_fragments.append(InputFragment(input_text, input_hash, timestamp))
        self.hash_counts[input_hash] += 1
        
        # Maintain window
        if len(self.recent_fragments) > self.window_size * 2:
            removed = self.recent_fragments.pop(0)
            self.hash_counts[removed.hash] -= 1
            if self.hash_counts[removed.hash] == 0:
                del self.hash_counts[removed.hash]
        
        return False, "NOVEL"

# Singleton instance
repetition_detector = RepetitionDetector(window_size=10, similarity_threshold=0.85)

def check_input_novelty(text: str, timestamp: float = None) -> dict:
    import time
    if timestamp is None:
        timestamp = time.time()
    is_repeat, reason = repetition_detector.detect(text, timestamp)
    return {
        "is_repetitive": is_repeat,
        "reason": reason,
        "should_deduplicate": is_repeat
    }