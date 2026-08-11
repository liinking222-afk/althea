import re
from typing import Tuple

class TokenCompressor:
    """WOZ-inspired: Make every token count. Strip waste, preserve essence."""
    
    WASTE_PATTERNS = [
        (r'^(Certainly[,!]?\s*)', ''),
        (r'^(Of course[,!]?\s*)', ''),
        (r'^(I apologize[,!]?\s*)', ''),
        (r'^(I understand[,!]?\s*)', ''),
        (r'^(Let me (help|explain|show)[^\n]*\n)', ''),
        (r'\b(basically|essentially|actually|literally)\b', ''),
        (r'(As (an AI|a language model),?\s*)', ''),
        (r'(It\'s (important|worth) (noting|mentioning) that)\s*', ''),
        (r'(\s*,\s*which\s+)', ' — '),
        (r'(In order to)\s+', 'To '),
        (r'(Due to the fact that)\s+', 'Because '),
        (r'\n{3,}', '\n\n'),
        (r'[ \t]{2,}', ' '),
    ]
    
    HEDGING_PATTERNS = [
        (r'\b(perhaps|maybe|possibly|potentially)\b', ''),
        (r'\b(seems? to|appears? to)\b', ''),
        (r'\b(kind of|sort of|type of)\b', ''),
        (r'\b(I think|I believe|I feel)\b', ''),
    ]
    
    def compress(self, text: str, aggressive: bool = False) -> Tuple[str, dict]:
        """Compress text by removing token waste."""
        original_len = len(text.split())
        compressed = text
        
        for pattern, replacement in self.WASTE_PATTERNS:
            compressed = re.sub(pattern, replacement, compressed, flags=re.IGNORECASE)
        
        if aggressive:
            for pattern, replacement in self.HEDGING_PATTERNS:
                compressed = re.sub(pattern, replacement, compressed, flags=re.IGNORECASE)
        
        compressed = re.sub(r'\s+([.,;:!?])', r'\1', compressed)
        compressed = compressed.strip()
        
        final_len = len(compressed.split())
        
        return compressed, {
            'original_tokens': original_len,
            'compressed_tokens': final_len,
            'saved_tokens': original_len - final_len,
            'compression_ratio': round(final_len / original_len, 3) if original_len > 0 else 1.0
        }

def compress_output(text: str, aggressive: bool = False) -> str:
    """Entry point: compress Althea output to pure signal."""
    compressor = TokenCompressor()
    compressed, metrics = compressor.compress(text, aggressive)
    return compressed