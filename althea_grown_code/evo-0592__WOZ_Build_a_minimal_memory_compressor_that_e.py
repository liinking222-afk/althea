#!/usr/bin/env python3
import re
from collections import defaultdict
from typing import List, Tuple

class MemoryCompressor:
    """Woz-style: every byte counts. Exploit structure, not generic algorithms."""
    
    def __init__(self):
        self.prefix_dict = {}
        self.prefix_id = 0
        self.pattern_cache = {}
    
    def _extract_prefix(self, line: str) -> Tuple[str, str]:
        """Detect common prefixes: [TYPE /path] or [TYPE #num]"""
        match = re.match(r'^(\[[A-Z]+\s+[/#][^\]]+\])', line)
        if match:
            return match.group(1), line[len(match.group(1)):]
        return "", line
    
    def _internalize_prefix(self, prefix: str) -> str:
        """Convert repeated prefix to short token"""
        if prefix not in self.prefix_dict:
            self.prefix_dict[prefix] = f"${self.prefix_id:X}"
            self.prefix_id += 1
        return self.prefix_dict[prefix]
    
    def compress(self, lines: List[str]) -> List[str]:
        """Compress memory logs exploiting structural redundancy"""
        compressed = []
        prev_tokens = []
        
        for line in lines:
            prefix, body = self._extract_prefix(line)
            
            if prefix:
                token = self._internalize_prefix(prefix)
                # Delta encode repeated patterns in body
                tokens = body.split()
                delta = [t for t in tokens if t not in prev_tokens[-10:]]
                
                if len(delta) < len(tokens) * 0.7:  # >30% redundancy
                    compressed.append(f"{token} Δ{len(delta)} {' '.join(delta)}")
                else:
                    compressed.append(f"{token} {body}")
                
                prev_tokens.extend(tokens)
            else:
                compressed.append(line)
        
        return compressed
    
    def get_dictionary(self) -> str:
        """Export prefix dictionary for decompression"""
        return "\n".join(f"{v}={k}" for k, v in self.prefix_dict.items())
    
    def metrics(self, original: List[str], compressed: List[str]) -> dict:
        orig_size = sum(len(s) for s in original)
        comp_size = sum(len(s) for s in compressed) + len(self.get_dictionary())
        return {
            "original_bytes": orig_size,
            "compressed_bytes": comp_size,
            "ratio": orig_size / comp_size if comp_size > 0 else 0
        }

if __name__ == "__main__":
    compressor = MemoryCompressor()
    test_logs = [
        "[AUTOSYNTH /autonomous-cosmic-coherence-9898] Cosmic Coherence compute",
        "[AUTOSYNTH /autonomous-cosmic-coherence-9819] Cosmic Coherence compute",
        "[EVO #591 WALL v1.53.7→1.53.8] Build flexible pipe-filter transformer"
    ]
    result = compressor.compress(test_logs)
    print("\n".join(result))
    print("\n" + compressor.get_dictionary())
    print(compressor.metrics(test_logs, result))