import hashlib
from collections import defaultdict
from datetime import datetime, timedelta

class ImaginationDeduplicator:
    def __init__(self, similarity_threshold=0.85, time_window_minutes=30):
        self.similarity_threshold = similarity_threshold
        self.time_window = timedelta(minutes=time_window_minutes)
        self.recent_imaginations = []
        self.pattern_signatures = defaultdict(int)
    
    def normalize_text(self, text):
        """Strip metadata and extract semantic core."""
        text = text.lower().strip()
        if text.startswith('[imagined]'):
            text = text[10:].strip()
        return ' '.join(text.split())
    
    def compute_signature(self, text):
        """Create semantic signature using sliding n-grams."""
        normalized = self.normalize_text(text)
        words = normalized.split()
        
        # Extract key semantic tokens (nouns, technical terms)
        key_tokens = [w for w in words if len(w) > 4][:15]
        signature = '|'.join(sorted(key_tokens))
        return hashlib.md5(signature.encode()).hexdigest()[:16]
    
    def jaccard_similarity(self, text1, text2):
        """Compute word-level similarity."""
        words1 = set(self.normalize_text(text1).split())
        words2 = set(self.normalize_text(text2).split())
        
        if not words1 or not words2:
            return 0.0
        
        intersection = len(words1 & words2)
        union = len(words1 | words2)
        return intersection / union if union > 0 else 0.0
    
    def is_novel(self, imagination_text):
        """Determine if this imagination adds value or is a loop."""
        now = datetime.now()
        signature = self.compute_signature(imagination_text)
        
        # Prune old entries outside time window
        self.recent_imaginations = [
            (ts, txt, sig) for ts, txt, sig in self.recent_imaginations
            if now - ts < self.time_window
        ]
        
        # Check signature frequency
        if self.pattern_signatures[signature] >= 2:
            return False
        
        # Check semantic similarity to recent imaginations
        for _, prev_text, _ in self.recent_imaginations[-10:]:
            similarity = self.jaccard_similarity(imagination_text, prev_text)
            if similarity >= self.similarity_threshold:
                return False
        
        # Novel - record it
        self.recent_imaginations.append((now, imagination_text, signature))
        self.pattern_signatures[signature] += 1
        return True
    
    def get_loop_statistics(self):
        """Return diagnostic info about detected loops."""
        return {
            'active_patterns': len(self.pattern_signatures),
            'recent_count': len(self.recent_imaginations),
            'repeated_signatures': sum(1 for v in self.pattern_signatures.values() if v > 1)
        }