#!/usr/bin/env python3
import re
import sys
from collections import defaultdict

class DualityExtractor:
    """Pragmatic pattern finder for structural inversions and symmetries."""
    
    INVERSION_PATTERNS = [
        (r'invert.*?topolog', 'topological_inversion'),
        (r'invert.*?phase|phase.*?invert', 'phase_inversion'),
        (r'resonance.*?invert|invert.*?resonance', 'resonance_inversion'),
    ]
    
    HOLLOWING_PATTERNS = [
        (r'hollow|remov.*?structure|strip.*?substrate', 'structural_hollowing'),
        (r'cancel.*?mutual|mutual.*?cancel', 'mutual_cancellation'),
    ]
    
    def __init__(self):
        self.dualities = defaultdict(list)
        self.symmetries = []
    
    def feed(self, text):
        """Duck-typed input - string or iterable of strings."""
        lines = [text] if isinstance(text, str) else text
        
        for line in lines:
            lower = line.lower()
            
            for pattern, tag in self.INVERSION_PATTERNS:
                if re.search(pattern, lower):
                    self.dualities['inversions'].append({'tag': tag, 'raw': line.strip()})
            
            for pattern, tag in self.HOLLOWING_PATTERNS:
                if re.search(pattern, lower):
                    self.dualities['subtractions'].append({'tag': tag, 'raw': line.strip()})
            
            # Find duality pairs (A→B suggests B→A symmetry)
            arrow_match = re.search(r'(\w+)\s*[→->]\s*(\w+)', line)
            if arrow_match:
                a, b = arrow_match.groups()
                self.symmetries.append({'forward': a, 'inverse': b, 'context': line.strip()})
    
    def get_composable_pairs(self):
        """Return duality pairs ready for lazy composition."""
        inv_tags = {d['tag'] for d in self.dualities['inversions']}
        sub_tags = {d['tag'] for d in self.dualities['subtractions']}
        
        return [
            {'inversion': inv, 'subtraction': sub, 'composable': True}
            for inv in inv_tags for sub in sub_tags
        ]
    
    def dump(self):
        """TIMTOWTDI output."""
        return {'dualities': dict(self.dualities), 'symmetries': self.symmetries}

if __name__ == '__main__':
    extractor = DualityExtractor()
    extractor.feed(sys.stdin)
    
    import json
    print(json.dumps(extractor.dump(), indent=2))
    
    pairs = extractor.get_composable_pairs()
    if pairs:
        print(f"\n# Composable pairs: {len(pairs)}", file=sys.stderr)