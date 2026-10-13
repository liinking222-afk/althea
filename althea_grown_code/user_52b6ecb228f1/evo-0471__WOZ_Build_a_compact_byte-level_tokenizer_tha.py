import re
from collections import defaultdict
from typing import Dict, Tuple

class ByteSemanticAnalyzer:
    """Wozniak-style efficiency tracker: every byte must earn its keep."""
    
    def __init__(self):
        self.semantic_patterns = {
            'intent': re.compile(r'INTENT:|intent:|goal:|objective:', re.I),
            'code': re.compile(r'