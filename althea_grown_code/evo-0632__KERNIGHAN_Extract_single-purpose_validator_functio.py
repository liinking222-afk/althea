#!/usr/bin/env python3
"""
validate.py - Single-purpose validation primitives
Each function answers ONE question. Compose them with pipes or chains.
"""

def is_weather_query(text: str) -> bool:
    """Does this text ask about weather?"""
    keywords = ['weather', 'temperature', 'forecast', 'climate', 'rain', 'snow']
    return any(word in text.lower() for word in keywords)

def is_capability_query(text: str) -> bool:
    """Does this text ask what Althea can do?"""
    patterns = ['what can', 'capabilities', 'what do', 'how do', 'can you']
    return any(pattern in text.lower() for pattern in patterns)

def is_system_command(text: str) -> bool:
    """Is this a system-level directive?"""
    return text.strip().startswith('[') and text.strip().endswith(']')

def is_evolution_marker(text: str) -> bool:
    """Is this an evolution event record?"""
    return '[EVO #' in text or '[GROWTH /' in text or '[AUTOSYNTH /' in text

def has_code_fence(text: str) -> bool:
    """Does this text contain fenced code?"""
    return '