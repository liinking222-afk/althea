#!/usr/bin/env python3
import re
import sys
from collections import defaultdict

def extract_code_blocks(text):
    """Extract fenced code blocks with metadata."""
    pattern = r'