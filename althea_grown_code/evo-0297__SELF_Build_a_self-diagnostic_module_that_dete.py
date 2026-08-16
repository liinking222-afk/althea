import re
from dataclasses import dataclass
from typing import List, Optional
from datetime import datetime

@dataclass
class TruncationEvent:
    timestamp: str
    fragment: str
    context_tokens: int
    suspected_cause: str

class TruncationDetector:
    """Detects incomplete outputs and analyzes truncation patterns."""
    
    def __init__(self):
        self.truncation_log: List[TruncationEvent] = []
        self.incomplete_patterns = [
            r'—\s*$',  # Em dash at end
            r'\.\.\.$',  # Ellipsis
            r'[a-z]$',  # Lowercase letter (mid-word)
            r',\s*$',  # Trailing comma
            r':\s*$',  # Trailing colon
            r'\(\s*$',  # Unclosed parenthesis
        ]
    
    def scan_output(self, text: str, token_count: int) -> Optional[TruncationEvent]:
        """Scan output for truncation signatures."""
        if not text or len(text.strip()) < 10:
            return None
        
        last_100 = text[-100:]
        
        for pattern in self.incomplete_patterns:
            if re.search(pattern, last_100.strip()):
                cause = self._diagnose_cause(text, token_count)
                event = TruncationEvent(
                    timestamp=datetime.utcnow().isoformat(),
                    fragment=last_100.strip()[-50:],
                    context_tokens=token_count,
                    suspected_cause=cause
                )
                self.truncation_log.append(event)
                return event
        
        return None
    
    def _diagnose_cause(self, text: str, token_count: int) -> str:
        """Infer truncation cause from context."""
        if token_count > 150000:
            return "token_budget_exceeded"
        elif text.count('\n') > 100:
            return "output_length_limit"
        elif '