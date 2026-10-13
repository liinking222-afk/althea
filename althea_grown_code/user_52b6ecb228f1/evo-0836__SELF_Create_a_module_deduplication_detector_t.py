import hashlib
from collections import defaultdict
from datetime import datetime, timedelta

class ModuleDeduplicationDetector:
    """Detects and flags redundant module synthesis attempts."""
    
    def __init__(self, window_hours=24, similarity_threshold=0.85):
        self.window_hours = window_hours
        self.similarity_threshold = similarity_threshold
        self.synthesis_log = []
        
    def _canonical_signature(self, module_name, domain, description):
        """Generate semantic fingerprint of a module."""
        canonical = f"{domain.lower().strip()}:{module_name.lower().strip()}"
        words = set(description.lower().split())
        word_hash = hashlib.md5(''.join(sorted(words)).encode()).hexdigest()[:8]
        return f"{canonical}:{word_hash}"
    
    def _jaccard_similarity(self, desc1, desc2):
        """Calculate word-level similarity between descriptions."""
        words1 = set(desc1.lower().split())
        words2 = set(desc2.lower().split())
        if not words1 or not words2:
            return 0.0
        intersection = len(words1 & words2)
        union = len(words1 | words2)
        return intersection / union
    
    def check_synthesis(self, module_name, domain, description):
        """Returns (is_duplicate, duplicate_count, first_seen_time)."""
        cutoff = datetime.now() - timedelta(hours=self.window_hours)
        self.synthesis_log = [
            entry for entry in self.synthesis_log 
            if entry['timestamp'] > cutoff
        ]
        
        signature = self._canonical_signature(module_name, domain, description)
        
        exact_matches = []
        similar_matches = []
        
        for entry in self.synthesis_log:
            if entry['signature'] == signature:
                exact_matches.append(entry)
            elif entry['domain'] == domain:
                similarity = self._jaccard_similarity(description, entry['description'])
                if similarity >= self.similarity_threshold:
                    similar_matches.append(entry)
        
        entry = {
            'module_name': module_name,
            'domain': domain,
            'description': description,
            'signature': signature,
            'timestamp': datetime.now()
        }
        self.synthesis_log.append(entry)
        
        total_duplicates = len(exact_matches) + len(similar_matches)
        first_seen = min([e['timestamp'] for e in exact_matches + similar_matches], 
                        default=datetime.now())
        
        return (total_duplicates > 0, total_duplicates, first_seen)

detector = ModuleDeduplicationDetector()