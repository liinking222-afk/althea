import re
from collections import Counter, defaultdict
from datetime import datetime
from typing import Dict, List, Tuple

class SynthesisDeduplicator:
    """Prevents redundant AUTOSYNTH operations by tracking patterns and timing."""
    
    def __init__(self, window_minutes: int = 60):
        self.window_minutes = window_minutes
        self.synthesis_log: List[Tuple[str, str, datetime]] = []
        self.pattern_cache: Dict[str, datetime] = {}
        
    def extract_pattern(self, memory_entry: str) -> str:
        """Extract the core pattern from AUTOSYNTH memory entries."""
        if "[AUTOSYNTH" not in memory_entry:
            return ""
        
        # Extract the capability slug
        match = re.search(r'/autonomous-([a-z-]+)-\d+', memory_entry)
        if not match:
            return ""
        
        return match.group(1)
    
    def should_synthesize(self, pattern: str, current_time: datetime = None) -> bool:
        """Determine if a pattern should trigger synthesis or is redundant."""
        if not pattern:
            return True
        
        if current_time is None:
            current_time = datetime.now()
        
        if pattern in self.pattern_cache:
            last_synthesis = self.pattern_cache[pattern]
            elapsed_minutes = (current_time - last_synthesis).total_seconds() / 60
            
            if elapsed_minutes < self.window_minutes:
                return False  # Too recent, skip
        
        return True
    
    def record_synthesis(self, pattern: str, current_time: datetime = None):
        """Record a synthesis event."""
        if current_time is None:
            current_time = datetime.now()
        
        self.pattern_cache[pattern] = current_time
        self.synthesis_log.append((pattern, "synthesized", current_time))
    
    def analyze_memory_stream(self, memory_entries: List[str]) -> Dict[str, int]:
        """Analyze recent memory for duplicate synthesis patterns."""
        pattern_counts = Counter()
        
        for entry in memory_entries:
            pattern = self.extract_pattern(entry)
            if pattern:
                pattern_counts[pattern] += 1
        
        return dict(pattern_counts)
    
    def get_redundancy_report(self, memory_entries: List[str]) -> str:
        """Generate a report of detected redundant patterns."""
        analysis = self.analyze_memory_stream(memory_entries)
        duplicates = {k: v for k, v in analysis.items() if v > 1}
        
        if not duplicates:
            return "No redundant synthesis patterns detected."
        
        report = f"Redundant patterns detected: {len(duplicates)}\n"
        for pattern, count in sorted(duplicates.items(), key=lambda x: -x[1]):
            report += f"  - {pattern}: {count} times\n"
        
        return report

# Singleton instance for Althea's use
deduplicator = SynthesisDeduplicator(window_minutes=30)