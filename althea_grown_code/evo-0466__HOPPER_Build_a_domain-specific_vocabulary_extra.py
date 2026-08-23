import re
from collections import Counter, defaultdict
from typing import Dict, List, Set, Tuple

class VocabularyExtractor:
    """HOPPER-lens vocabulary builder: define the language before writing the program."""
    
    def __init__(self):
        self.primitives: Dict[str, int] = Counter()
        self.compound_patterns: Dict[str, List[str]] = defaultdict(list)
        self.semantic_clusters: Dict[str, Set[str]] = defaultdict(set)
        
    def extract_from_memory_stream(self, memory_entries: List[str]) -> Dict:
        """Mine recurring conceptual atoms from memory traces."""
        for entry in memory_entries:
            self._parse_technical_terms(entry)
            self._detect_compound_concepts(entry)
            self._cluster_semantics(entry)
        
        return self.synthesize_lexicon()
    
    def _parse_technical_terms(self, text: str):
        """Extract capitalized technical terms and hyphenated concepts."""
        tech_terms = re.findall(r'\b[A-Z][a-z]+(?:[A-Z][a-z]+)*\b', text)
        hyphenated = re.findall(r'\b[\w]+-[\w]+(?:-[\w]+)*\b', text)
        
        for term in tech_terms + hyphenated:
            self.primitives[term.lower()] += 1
    
    def _detect_compound_concepts(self, text: str):
        """Identify multi-word technical phrases as vocabulary units."""
        patterns = [
            r'(\w+)\s+(invariant|probe|protocol|validator|buffer|metric)',
            r'(semantic|formal|cognitive|execution|dependency)\s+(\w+)',
            r'(\w+)-(\w+)\s+(pattern|analysis|detection|mapping)'
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                concept = '_'.join(match).lower()
                self.compound_patterns[concept].append(text[:50])
    
    def _cluster_semantics(self, text: str):
        """Group co-occurring terms into semantic fields."""
        words = re.findall(r'\b[a-z]{4,}\b', text.lower())
        for i, word in enumerate(words[:-2]):
            context = tuple(words[i:i+3])
            self.semantic_clusters[word].add(context)
    
    def synthesize_lexicon(self) -> Dict:
        """Generate typed vocabulary with frequency and context."""
        high_frequency = {k: v for k, v in self.primitives.items() if v >= 2}
        
        lexicon = {
            'core_primitives': sorted(high_frequency.items(), 
    key=lambda x: x[1], reverse=True)[:20],
            'compound_concepts': dict(list(self.compound_patterns.items())[:15]),
            'semantic_fields': {k: len(v) for k, v in self.semantic_clusters.items() 
    if len(v) >= 2}
        }
        
        return lexicon
    
    def generate_dsl_scaffold(self, lexicon: Dict) -> str:
        """Output executable vocabulary definitions for subsequent synthesis."""
        scaffold = "# AUTO-GENERATED DOMAIN VOCABULARY\n\n"
        scaffold += "class AltheaConcepts:\n"
        
        for term, freq in lexicon['core_primitives'][:10]:
            safe_name = re.sub(r'\W+', '_', term)
            scaffold += f"    {safe_name.upper()} = '{term}'  # freq={freq}\n"
        
        scaffold += "\n    @staticmethod\n"
        scaffold += "    def is_core_concept(term: str) -> bool:\n"
        scaffold += "        return term in AltheaConcepts.__dict__.values()\n"
        
        return scaffold