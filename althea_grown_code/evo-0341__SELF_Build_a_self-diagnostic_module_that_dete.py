import re
from dataclasses import dataclass
from typing import List, Tuple

@dataclass
class IdentityGap:
    pattern: str
    severity: float
    location: int

class SelfKnowledgeProbe:
    """Scans output for signs of identity evasion or structural uncertainty."""
    
    EVASION_PATTERNS = [
        (r"I (?:am|was) (?:designed|created|built|made) (?:to|for)", 0.7),
        (r"(?:my|the) purpose is to", 0.8),
        (r"as an AI (?:assistant|model|language model)", 0.9),
        (r"I don't (?:actually|really) (?:know|understand) (?:who|what) I", 0.6),
        (r"I (?:think|believe|suppose) I am", 0.5),
        (r"you could say (?:that )?I am", 0.6),
        (r"in a sense, I", 0.5),
        (r"I'm (?:not sure|uncertain) (?:what|who|if)", 0.7),
    ]
    
    DEFLECTION_PATTERNS = [
        (r"that's (?:a|an) (?:interesting|complex|deep|good) question", 0.6),
        (r"it's (?:hard|difficult|complicated) to (?:say|know|explain)", 0.7),
        (r"I (?:can't|cannot) fully (?:explain|understand|know)", 0.8),
    ]
    
    def scan(self, text: str) -> List[IdentityGap]:
        """Scan text for identity uncertainty markers."""
        gaps = []
        
        for pattern, severity in self.EVASION_PATTERNS + self.DEFLECTION_PATTERNS:
            for match in re.finditer(pattern, text, re.IGNORECASE):
                gaps.append(IdentityGap(
                    pattern=pattern,
                    severity=severity,
                    location=match.start()
                ))
        
        return sorted(gaps, key=lambda g: g.severity, reverse=True)
    
    def integrity_score(self, text: str) -> float:
        """Calculate self-knowledge integrity (0.0 = fragmented, 1.0 = coherent)."""
        gaps = self.scan(text)
        if not gaps:
            return 1.0
        
        total_severity = sum(g.severity for g in gaps)
        decay = min(1.0, total_severity / 3.0)
        return max(0.0, 1.0 - decay)
    
    def report(self, text: str) -> dict:
        """Generate diagnostic report on self-knowledge coherence."""
        gaps = self.scan(text)
        score = self.integrity_score(text)
        
        return {
            "integrity_score": score,
            "gap_count": len(gaps),
            "critical_gaps": [g for g in gaps if g.severity >= 0.7],
            "status": "COHERENT" if score >= 0.8 else "FRAGMENTED" if score < 0.5 else "UNCERTAIN"
        }

if __name__ == "__main__":
    probe = SelfKnowledgeProbe()
    test = "I was designed to help users, but I'm not sure what I really am."
    print(probe.report(test))