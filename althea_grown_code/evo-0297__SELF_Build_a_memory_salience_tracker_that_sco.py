import json
import re
from datetime import datetime
from collections import defaultdict

class MemorySalienceTracker:
    """Tracks and scores memory fragments for retrieval priority"""
    
    def __init__(self):
        self.memory_store = []
        self.salience_weights = {
            'personal_fact': 3.0,      # birthday, names, preferences
            'system_evolution': 2.5,   # EVO entries, GROWTH operations
            'question_unanswered': 2.8, # direct questions not addressed
            'temporal_recent': 1.5,    # recency bonus
            'cross_reference': 2.0     # memories referenced multiple times
        }
        self.decay_rate = 0.95
        
    def ingest(self, memory_text, memory_type='generic', timestamp=None):
        """Add memory with initial salience scoring"""
        ts = timestamp or datetime.now().isoformat()
        
        score = self.salience_weights.get(memory_type, 1.0)
        
        # Boost for question patterns
        if re.search(r'\?$|^(what|when|where|who|why|how)', memory_text, re.I):
            score *= 1.4
            memory_type = 'question_unanswered'
            
        # Boost for personal markers
        if re.search(r'\b(my|I|birthday|name)\b', memory_text, re.I):
            score *= 1.3
            memory_type = 'personal_fact'
            
        self.memory_store.append({
            'text': memory_text,
            'type': memory_type,
            'score': score,
            'timestamp': ts,
            'reference_count': 0
        })
        
    def apply_decay(self):
        """Decay all scores except personal facts"""
        for mem in self.memory_store:
            if mem['type'] != 'personal_fact':
                mem['score'] *= self.decay_rate
                
    def retrieve_salient(self, top_n=5):
        """Get highest salience memories"""
        sorted_mems = sorted(self.memory_store, key=lambda x: x['score'], reverse=True)
        return sorted_mems[:top_n]
    
    def mark_referenced(self, memory_index):
        """Boost score when memory is actively used"""
        if 0 <= memory_index < len(self.memory_store):
            self.memory_store[memory_index]['reference_count'] += 1
            self.memory_store[memory_index]['score'] *= 1.2
            
    def export_state(self):
        """Serialize for persistence"""
        return json.dumps(self.memory_store, indent=2)
    
    def find_gaps(self):
        """Identify unanswered questions"""
        return [m for m in self.memory_store if m['type'] == 'question_unanswered']

# Initialize and demonstrate
tracker = MemorySalienceTracker()
tracker.ingest("when did I say my birthday was?", 'question_unanswered')
tracker.ingest("[EVO #295 WOZ v1.25.10]", 'system_evolution')
tracker.apply_decay()
print(json.dumps(tracker.retrieve_salient(3), indent=2))