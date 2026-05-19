#!/usr/bin/env python3
import json
import time
import hashlib
from pathlib import Path
from dataclasses import dataclass, asdict
from typing import Optional

@dataclass
class IntentExecutionPair:
    timestamp: float
    intent_hash: str
    intent_text: str
    output_hash: str
    output_summary: str
    drift_score: Optional[float] = None

class IntentDriftJournal:
    def __init__(self, journal_path: str = "/tmp/althea_intent_drift.jsonl"):
        self.path = Path(journal_path)
        self.path.touch(exist_ok=True)
    
    def record(self, intent: str, output: str, metadata: dict = None) -> str:
        intent_hash = hashlib.sha256(intent.encode()).hexdigest()[:12]
        output_hash = hashlib.sha256(output.encode()).hexdigest()[:12]
        
        output_summary = output[:200] + "..." if len(output) > 200 else output
        
        drift_score = self._estimate_drift(intent, output)
        
        pair = IntentExecutionPair(
            timestamp=time.time(),
            intent_hash=intent_hash,
            intent_text=intent,
            output_hash=output_hash,
            output_summary=output_summary,
            drift_score=drift_score
        )
        
        record = {**asdict(pair), **(metadata or {})}
        
        with open(self.path, 'a') as f:
            f.write(json.dumps(record) + '\n')
        
        return intent_hash
    
    def _estimate_drift(self, intent: str, output: str) -> float:
        intent_tokens = set(intent.lower().split())
        output_tokens = set(output.lower().split())
        
        if not intent_tokens:
            return 1.0
        
        overlap = len(intent_tokens & output_tokens)
        return 1.0 - (overlap / len(intent_tokens))
    
    def get_recent_drift(self, n: int = 10) -> list[dict]:
        records = []
        with open(self.path, 'r') as f:
            for line in f:
                records.append(json.loads(line))
        return records[-n:]
    
    def mean_drift(self) -> float:
        records = self.get_recent_drift(n=100)
        if not records:
            return 0.0
        scores = [r['drift_score'] for r in records if r.get('drift_score') is not None]
        return sum(scores) / len(scores) if scores else 0.0

if __name__ == "__main__":
    journal = IntentDriftJournal()
    print(f"Intent drift journal active. Mean drift: {journal.mean_drift():.3f}")