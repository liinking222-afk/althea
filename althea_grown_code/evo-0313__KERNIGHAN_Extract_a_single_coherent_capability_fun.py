#!/usr/bin/env python3
import re
from collections import Counter
from pathlib import Path

def synthesize_capability_from_dialogue(dialogue_text):
    """Extract ONE capability from dialogue. Return executable function or None."""
    
    # Find code-like patterns: function signatures, clear intent statements
    intent_pattern = r'(?:build|create|write|make)\s+(?:a\s+)?([a-z_][a-z0-9_\s]+?)(?:\s+that|\s+to|\s+for)'
    intents = re.findall(intent_pattern, dialogue_text.lower())
    
    if not intents:
        return None
    
    # Pick highest frequency intent (strongest signal)
    primary_intent = Counter(intents).most_common(1)[0][0].strip()
    
    # Extract code blocks near this intent
    code_blocks = re.findall(r'