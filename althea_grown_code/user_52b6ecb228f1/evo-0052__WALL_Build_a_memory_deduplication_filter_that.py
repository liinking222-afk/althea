#!/usr/bin/env python3
import re
from collections import defaultdict
from hashlib import sha256

class MemoryDeduplicator:
    """Pragmatic memory dedup: canonicalize patterns, track occurrences, compress storage."""
    
    def __init__(self):
        self.patterns = [
            (r'\[NETWORK-PROFILE\]\s+declared\s+ssid=([\'"])([^\'"]+)\1\s+security=(\w+)\s+password=(\w+)\..*', 
             lambda m: f"[NETWORK-PROFILE] ssid={m.group(2)} security={m.group(3)} password={m.group(4)}"),
            (r'\[(\w+)\s+node:(\S+)\s+stream:(\S+)\]\s+(.+)',
             lambda m: f"[{m.group(1)}:{m.group(2)}:{m.group(3)}] {m.group(4)[:80]}"),
        ]
        self.seen = defaultdict(int)
        self.canonical = {}
    
    def fingerprint(self, text):
        """Duck-typed hash: if it quacks like duplicate memory, hash it the same."""
        for pattern, canonicalizer in self.patterns:
            match = re.match(pattern, text, re.IGNORECASE)
            if match:
                canonical = canonicalizer(match)
                fp = sha256(canonical.encode()).hexdigest()[:16]
                self.canonical[fp] = canonical
                return fp
        return sha256(text.encode()).hexdigest()[:16]
    
    def process(self, memory_item):
        """TIMTOWTDI: return (should_store, transformed_item)"""
        fp = self.fingerprint(memory_item)
        self.seen[fp] += 1
        
        if self.seen[fp] == 1:
            return (True, memory_item)
        elif self.seen[fp] <= 3:
            canonical = self.canonical.get(fp, memory_item)
            return (True, f"{canonical} [×{self.seen[fp]}]")
        elif self.seen[fp] == 4:
            canonical = self.canonical.get(fp, memory_item)
            return (True, f"{canonical} [×{self.seen[fp]}, further occurrences suppressed]")
        else:
            return (False, None)
    
    def report(self):
        """Optimize for the reader: show what's being compressed."""
        return {fp: (count, self.canonical.get(fp, "non-canonical")) 
                for fp, count in self.seen.items() if count > 1}

if __name__ == "__main__":
    dedup = MemoryDeduplicator()
    test_memories = [
        "[NETWORK-PROFILE] declared ssid='AlthEa-Test-Net' security=WPA2 password=set. NOTE: browsers cannot join wi-fi natively — profile recorded only.",
        "[NETWORK-PROFILE] declared ssid='AlthEa-Test-Net' security=WPA2 password=set. NOTE: browsers cannot join wi-fi natively — profile recorded only.",
        "[REFLECTION node:NODE-0242 stream:pairing:usb] Iterative probing cycles demonstrate progressive refinement",
    ]
    for mem in test_memories:
        should_store, transformed = dedup.process(mem)
        if should_store:
            print(f"STORE: {transformed}")