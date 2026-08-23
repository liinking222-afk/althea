#!/usr/bin/env python3
import re
import subprocess
import sys
from pathlib import Path

INTERPRETERS = {
    'python': ['python3', '-u'],
    'javascript': ['node'],
    'bash': ['bash'],
    'rust': ['rust-script'],  # or compile-then-run
    'go': ['go', 'run'],
    'typescript': ['deno', 'run', '--allow-all'],
}

def extract_fenced_code(text):
    """Extract language and code from triple-backtick fenced blocks."""
    pattern = r'