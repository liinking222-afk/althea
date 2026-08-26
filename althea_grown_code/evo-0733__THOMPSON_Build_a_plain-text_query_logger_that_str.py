#!/usr/bin/env python3
import sys
import json
import hashlib
from datetime import datetime
from pathlib import Path

class QueryStreamLogger:
    """Thompson-style plain-text query stream for pipe composition"""
    
    def __init__(self, log_path=None):
        self.log_path = Path(log_path) if log_path else None
        
    def log(self, query, metadata=None):
        """Output plain-text line: timestamp|hash|query"""
        ts = datetime.utcnow().isoformat()
        query_hash = hashlib.sha256(query.encode()).hexdigest()[:8]
        line = f"{ts}|{query_hash}|{query}"
        
        # Always to stdout for piping
        print(line, flush=True)
        
        # Optionally to file
        if self.log_path:
            with open(self.log_path, 'a') as f:
                f.write(line + '\n')
        
        return query_hash
    
    def detect_repetition(self, query, window=10):
        """Pipe to this: detects recent repetitions"""
        if not self.log_path or not self.log_path.exists():
            return False
            
        recent = []
        with open(self.log_path, 'r') as f:
            recent = f.readlines()[-window:]
        
        query_hash = hashlib.sha256(query.encode()).hexdigest()[:8]
        return sum(1 for line in recent if f"|{query_hash}|" in line) > 1

def main():
    """CLI tool: echo queries | ./query_stream.py"""
    logger = QueryStreamLogger(log_path=".althea_queries.log")
    
    for line in sys.stdin:
        query = line.strip()
        if query:
            hash_id = logger.log(query)
            if logger.detect_repetition(query):
                print(f"REPEAT:{hash_id}", file=sys.stderr)

if __name__ == "__main__":
    main()