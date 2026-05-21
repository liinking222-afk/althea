#!/usr/bin/env python3
import re
import sys
import json

class EvoLogParser:
    """Parse evolution logs into composable streams - TMTOWTDI applied to self-reflection."""
    
    PATTERNS = {
        'evo': r'\[EVO #(\d+) (\w+) v([\d.]+)→([\d.]+)\]',
        'growth': r'\[GROWTH /([\w-]+)\]',
        'intent': r'INTENT:\s*(.+?)(?:\n|$)',
        'lang': r'LANGUAGE:\s*(\w+)',
        'delta': r'DELTA:\s*(.+?)(?:\n|$)',
        'code_block': r'