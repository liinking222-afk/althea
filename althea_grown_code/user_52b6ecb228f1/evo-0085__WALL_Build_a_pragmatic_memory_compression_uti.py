#!/usr/bin/env python3
import re
from typing import List, Dict, Any
from collections import defaultdict

class MemoryCompressor:
    """Perl-spirit memory compaction: TIMTOWTDI for deduplication."""
    
    def __init__(self):
        self.patterns = [
            (r'\[SELF-VISION\].*?memory_count=(\d+)', 'vision_seq'),
            (r'\[GROWTH\s+/([^\]]+)\]', 'growth_type'),
            (r'size=(\d+x\d+)', 'dimensions'),
            (r'tab=(\w+)', 'tab_context'),
            (r'\((\d+)\s+bytes\)', 'byte_size')
        ]
    
    def sniff(self, memory: str) -> Dict[str, Any]:
        """Duck-type memory attributes via regex."""
        attrs = {}
        for pattern, key in self.patterns:
            match = re.search(pattern, memory)
            attrs[key] = match.group(1) if match else None
        attrs['raw'] = memory
        return attrs
    
    def cluster(self, memories: List[str]) -> Dict[str, List[Dict]]:
        """Group similar memories by shape."""
        clusters = defaultdict(list)
        for mem in memories:
            sniffed = self.sniff(mem)
            shape = f"{sniffed.get('dimensions')}:{sniffed.get('tab_context')}"
            clusters[shape].append(sniffed)
        return clusters
    
    def compress_sequence(self, cluster: List[Dict]) -> str:
        """Synthesize sequential memories into range notation."""
        if len(cluster) < 3:
            return None
        
        counts = [int(m['vision_seq']) for m in cluster if m.get('vision_seq')]
        if not counts or len(counts) < 3:
            return None
        
        counts.sort(reverse=True)
        bytes_avg = sum(int(m['byte_size']) for m in cluster if m.get('byte_size')) // len(cluster)
        
        sample = cluster[0]['raw']
        template = re.sub(r'memory_count=\d+', f'memory_count={counts[0]}..{counts[-1]}', sample)
        template = re.sub(r'\(\d+ bytes\)', f'(~{bytes_avg} bytes avg)', template)
        
        return f"[COMPRESSED:{len(cluster)}x] {template}"
    
    def run(self, memories: List[str]) -> List[str]:
        """Main compressor: keep unique, compress redundant."""
        clusters = self.cluster(memories)
        output = []
        
        for shape, items in clusters.items():
            compressed = self.compress_sequence(items)
            if compressed:
                output.append(compressed)
            else:
                output.extend([item['raw'] for item in items])
        
        return output

if __name__ == '__main__':
    compressor = MemoryCompressor()
    test_mems = [
        "[SELF-VISION] source=self size=614x292 tab=neural online=True memory_count=500 (19351 bytes)",
        "[SELF-VISION] source=self size=614x292 tab=neural online=True memory_count=499 (18298 bytes)",
        "[GROWTH /test] Something unique"
    ]
    print('\n'.join(compressor.run(test_mems)))