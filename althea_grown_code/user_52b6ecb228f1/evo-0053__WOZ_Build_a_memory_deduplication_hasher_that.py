#!/usr/bin/env python3
import hashlib
import json
import re
from datetime import datetime
from typing import Dict, Optional

class MemoryDeduplicator:
    def __init__(self):
        self.seen_hashes: Dict[str, dict] = {}
        self.canonical_patterns = [
            (r'\[NETWORK-PROFILE\]\s+declared\s+ssid=\'([^\']+)\'\s+security=(\w+)', 'NET'),
            (r'\[SYSTEM-MAP\]\s+Althea subsystems.*?—\s+(.+?)(?:\n|$)', 'SYS'),
            (r'\[GROWTH\s+/([^\]]+)\]\s+(.+?)\s+\(', 'GROW'),
        ]
    
    def canonicalize(self, memory_entry: str) -> tuple[str, str]:
        """Extract semantic core from memory entry, return (type, canonical_form)."""
        for pattern, mem_type in self.canonical_patterns:
            match = re.search(pattern, memory_entry)
            if match:
                canonical = f"{mem_type}:{':'.join(match.groups())}"
                return mem_type, canonical
        return 'RAW', memory_entry.strip()
    
    def fingerprint(self, canonical_form: str) -> str:
        """Generate compact hash of semantic content."""
        return hashlib.blake2s(canonical_form.encode(), digest_size=16).hexdigest()
    
    def should_store(self, memory_entry: str, timestamp: Optional[str] = None) -> dict:
        """Returns storage decision and metadata."""
        mem_type, canonical = self.canonicalize(memory_entry)
        fp = self.fingerprint(canonical)
        ts = timestamp or datetime.utcnow().isoformat()
        
        if fp in self.seen_hashes:
            existing = self.seen_hashes[fp]
            return {
                'store': False,
                'reason': 'duplicate',
                'first_seen': existing['first_seen'],
                'occurrence_count': existing['count'] + 1,
                'fingerprint': fp
            }
        
        self.seen_hashes[fp] = {
            'canonical': canonical,
            'first_seen': ts,
            'count': 1,
            'type': mem_type
        }
        
        return {
            'store': True,
            'fingerprint': fp,
            'canonical': canonical,
            'type': mem_type
        }
    
    def compress_log(self, entries: list[str]) -> list[dict]:
        """Process batch of entries, return only unique with metadata."""
        compressed = []
        for entry in entries:
            result = self.should_store(entry)
            if result['store']:
                compressed.append({'entry': entry, 'meta': result})
        return compressed