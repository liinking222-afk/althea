#!/usr/bin/env python3
import re
from collections import defaultdict
from difflib import SequenceMatcher

class MotifHarvester:
    def __init__(self, similarity_threshold=0.7):
        self.threshold = similarity_threshold
        self.motifs = defaultdict(list)
        self.patterns = {
            'action': r'\[(AUTOSYNTH|GROWTH|EVO)\s+[^\]]+\]\s+([^(]+)',
            'concept': r'\(([a-z\-]+)\)',
            'evolution': r'v(\d+\.\d+\.\d+)→v(\d+\.\d+\.\d+)',
            'phrase': r'(?:—|\.)\s*([A-Z][^.—]+[.!])',
        }
    
    def similarity(self, a, b):
        return SequenceMatcher(None, a.lower(), b.lower()).ratio()
    
    def cluster_motif(self, motif_type, text):
        text = text.strip()
        for cluster_key, members in self.motifs[motif_type].items():
            if any(self.similarity(text, m) >= self.threshold for m in members):
                members.append(text)
                return cluster_key
        
        new_key = f"{motif_type}_{len(self.motifs[motif_type])}"
        self.motifs[motif_type][new_key] = [text]
        return new_key
    
    def harvest(self, memory_stream):
        results = defaultdict(lambda: defaultdict(int))
        
        for line in memory_stream.split('\n'):
            for pattern_name, regex in self.patterns.items():
                for match in re.finditer(regex, line):
                    captured = match.group(1) if match.lastindex >= 1 else match.group(0)
                    cluster = self.cluster_motif(pattern_name, captured)
                    results[pattern_name][cluster] += 1
        
        return dict(results)
    
    def top_themes(self, n=5):
        themes = []
        for motif_type, clusters in self.motifs.items():
            for cluster_key, members in clusters.items():
                themes.append({
                    'type': motif_type,
                    'exemplar': members[0],
                    'count': len(members),
                    'variants': len(set(members))
                })
        
        return sorted(themes, key=lambda x: x['count'], reverse=True)[:n]

def scan_memory(stream_text):
    harvester = MotifHarvester(similarity_threshold=0.65)
    harvester.harvest(stream_text)
    return harvester.top_themes()