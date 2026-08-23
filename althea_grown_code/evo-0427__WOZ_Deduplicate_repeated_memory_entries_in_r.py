#!/usr/bin/env python3
"""memory_dedup.py - Rolling hash deduplication for Althea's memory stream"""

import hashlib
import sys
from collections import deque
from typing import Set, Optional

class MemoryDeduplicator:
    """Woz-style: minimal state, maximum efficiency. One pass, O(1) lookup."""
    
    def __init__(self, window_size: int = 100, similarity_threshold: int = 32):
        self.seen_hashes: Set[str] = set()
        self.recent_queue: deque = deque(maxlen=window_size)
        self.threshold = similarity_threshold
        self.stats = {"total": 0, "unique": 0, "dupes": 0}
    
    def _fingerprint(self, text: str) -> str:
        """Generate compact hash fingerprint from first N chars of content."""
        normalized = text.strip()[:self.threshold]
        return hashlib.blake2s(normalized.encode(), digest_size=8).hexdigest()
    
    def should_keep(self, memory_line: str) -> bool:
        """Returns True if memory is novel enough to keep."""
        self.stats["total"] += 1
        
        # Extract content after timestamp/marker
        content = memory_line.split("] ", 1)[-1] if "]" in memory_line else memory_line
        fingerprint = self._fingerprint(content)
        
        if fingerprint in self.seen_hashes:
            self.stats["dupes"] += 1
            return False
        
        self.seen_hashes.add(fingerprint)
        self.recent_queue.append(fingerprint)
        self.stats["unique"] += 1
        return True
    
    def process_stream(self, input_stream=sys.stdin, output_stream=sys.stdout):
        """Filter memory stream: emit only unique entries."""
        for line in input_stream:
            if self.should_keep(line):
                output_stream.write(line)
        
        # Compression ratio to stderr
        if self.stats["total"] > 0:
            ratio = 100 * (1 - self.stats["unique"] / self.stats["total"])
            sys.stderr.write(f"# Compressed {ratio:.1f}% ({self.stats['dupes']}/{self.stats['total']})\n")

if __name__ == "__main__":
    deduper = MemoryDeduplicator()
    deduper.process_stream()