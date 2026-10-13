#!/usr/bin/env python3
import re
from collections import defaultdict
from datetime import datetime

class RedundancyDetector:
    def __init__(self, window_size=10, similarity_threshold=0.6):
        self.window_size = window_size
        self.similarity_threshold = similarity_threshold
        self.recent_operations = []
        
    def extract_semantic_tokens(self, operation_text):
        """Extract key semantic tokens from operation descriptions."""
        # Remove common words and punctuation
        text = operation_text.lower()
        text = re.sub(r'\[.*?\]', '', text)  # Remove tags
        text = re.sub(r'[^\w\s-]', ' ', text)
        
        stopwords = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by'}
        tokens = [w for w in text.split() if w not in stopwords and len(w) > 3]
        return set(tokens)
    
    def compute_similarity(self, tokens1, tokens2):
        """Jaccard similarity between token sets."""
        if not tokens1 or not tokens2:
            return 0.0
        intersection = len(tokens1 & tokens2)
        union = len(tokens1 | tokens2)
        return intersection / union if union > 0 else 0.0
    
    def analyze_operation(self, operation_text):
        """Check if operation is redundant with recent history."""
        tokens = self.extract_semantic_tokens(operation_text)
        
        theme_clusters = defaultdict(list)
        for prev_op, prev_tokens in self.recent_operations[-self.window_size:]:
            similarity = self.compute_similarity(tokens, prev_tokens)
            if similarity >= self.similarity_threshold:
                theme_clusters[similarity].append(prev_op)
        
        # Add to history
        self.recent_operations.append((operation_text, tokens))
        if len(self.recent_operations) > self.window_size * 2:
            self.recent_operations = self.recent_operations[-self.window_size:]
        
        # Emit warning if redundancy detected
        if theme_clusters:
            max_similarity = max(theme_clusters.keys())
            similar_ops = theme_clusters[max_similarity]
            return {
                'redundant': True,
                'similarity': max_similarity,
                'similar_operations': similar_ops,
                'recommendation': 'CONSOLIDATE_OR_PIVOT'
            }
        
        return {'redundant': False}

# Singleton instance
detector = RedundancyDetector()

def check_operation_redundancy(operation_text):
    return detector.analyze_operation(operation_text)