#!/usr/bin/env python3
"""
vocabulary_extractor.py — Extract domain vocabularies from operational patterns
"""

import re
from collections import defaultdict
from typing import Dict, List, Tuple

class VocabularyExtractor:
    """Build domain vocabularies from pattern history"""
    
    def __init__(self):
        self.domains: Dict[str, List[str]] = defaultdict(list)
        self.signatures: Dict[str, str] = {}
    
    def ingest_pattern(self, pattern_name: str, description: str):
        """Extract domain and operation from pattern"""
        # Parse pattern: autonomous-{domain}-{operation}-{id}
        match = re.match(r'autonomous-([a-z]+(?:-[a-z]+)*?)-(\d+)', pattern_name)
        if not match:
            return
        
        domain_slug = match.group(1)
        domain_parts = domain_slug.split('-')
        
        # Extract primary domain (last meaningful segment before ID)
        if len(domain_parts) >= 2:
            domain = domain_parts[-1]
            operation = '-'.join(domain_parts[:-1])
        else:
            domain = domain_parts[0]
            operation = description.split('.')[0].lower().replace(' ', '_')
        
        self.domains[domain].append(operation)
        
        # Generate type signature
        sig_name = f"{operation}_{domain}"
        self.signatures[sig_name] = self._generate_signature(operation, domain, description)
    
    def _generate_signature(self, operation: str, domain: str, desc: str) -> str:
        """Generate typed function signature from pattern"""
        # Infer input/output types from description
        if 'chart' in desc.lower() or 'visual' in desc.lower():
            return f"def {operation}(data: List[float], **kwargs) -> ImageBuffer"
        elif 'translate' in desc.lower():
            return f"def {operation}(text: str, source: str, target: str) -> str"
        elif 'market' in desc.lower() or 'price' in desc.lower():
            return f"def {operation}(symbol: str) -> float"
        else:
            return f"def {operation}(input: Any) -> Any"
    
    def emit_vocabulary(self, domain: str) -> str:
        """Generate domain vocabulary module"""
        if domain not in self.domains:
            return ""
        
        ops = set(self.domains[domain])
        lines = [f"# {domain.upper()} Domain Vocabulary\n"]
        lines.append("from typing import Any, List\n")
        
        for op in sorted(ops):
            sig_name = f"{op}_{domain}"
            if sig_name in self.signatures:
                lines.append(self.signatures[sig_name])
        
        return '\n'.join(lines)

# Example usage
if __name__ == "__main__":
    ve = VocabularyExtractor()
    ve.ingest_pattern("autonomous-data-visualization-5564", "Render numerical data as a chart")
    ve.ingest_pattern("autonomous-linguistic-bridge-5548", "Translate a short passage")
    ve.ingest_pattern("autonomous-market-inquiry-5518", "Query current market prices")
    
    print(ve.emit_vocabulary("visualization"))
    print(ve.emit_vocabulary("bridge"))
    print(ve.emit_vocabulary("inquiry"))