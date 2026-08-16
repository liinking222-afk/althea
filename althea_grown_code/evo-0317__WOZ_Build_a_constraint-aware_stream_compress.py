#!/usr/bin/env python3
import sys
import json
import hashlib
from collections import deque

class StreamCompressor:
    def __init__(self, window_size=5, similarity_threshold=0.6):
        self.window = deque(maxlen=window_size)
        self.seen_hashes = set()
        
    def token_set(self, text):
        return set(text.lower().split())
    
    def jaccard_similarity(self, set1, set2):
        if not set1 or not set2:
            return 0.0
        intersection = len(set1 & set2)
        union = len(set1 | set2)
        return intersection / union if union > 0 else 0.0
    
    def semantic_hash(self, event):
        key_fields = f"{event.get('type', '')}:{event.get('category', '')}:{' '.join(sorted(self.token_set(event.get('content', ''))))}"
        return hashlib.blake2s(key_fields.encode(), digest_size=16).hexdigest()
    
    def merge_events(self, base, incoming):
        merged = base.copy()
        merged['content'] = f"{base['content']} | {incoming['content']}"
        merged['merged_count'] = merged.get('merged_count', 1) + 1
        return merged
    
    def process_event(self, event):
        sem_hash = self.semantic_hash(event)
        
        if sem_hash in self.seen_hashes:
            return None
        
        event_tokens = self.token_set(event.get('content', ''))
        
        for i, window_event in enumerate(self.window):
            window_tokens = self.token_set(window_event.get('content', ''))
            similarity = self.jaccard_similarity(event_tokens, window_tokens)
            
            if similarity >= 0.6 and event.get('type') == window_event.get('type'):
                merged = self.merge_events(window_event, event)
                self.window[i] = merged
                self.seen_hashes.add(sem_hash)
                return None
        
        self.window.append(event)
        self.seen_hashes.add(sem_hash)
        return event

compressor = StreamCompressor()
for line in sys.stdin:
    try:
        event = json.loads(line.strip())
        output = compressor.process_event(event)
        if output:
            print(json.dumps(output))
    except:
        continue