#!/usr/bin/env python3
import re
import subprocess
import sys
import json
from typing import Dict, Optional

VALIDATORS = {
    'python': lambda code: subprocess.run(['python3', '-m', 'py_compile', '-'], 
    input=code, capture_output=True, text=True),
    'javascript': lambda code: subprocess.run(['node', '--check', '-'],
    input=code, capture_output=True, text=True),
    'bash': lambda code: subprocess.run(['bash', '-n', '-'],
    input=code, capture_output=True, text=True),
    'rust': lambda code: subprocess.run(['rustc', '--crate-type', 'lib', '-', '-o', '/dev/null'],
    input=code, capture_output=True, text=True),
    'typescript': lambda code: subprocess.run(['tsc', '--noEmit', '--stdin'],
    input=code, capture_output=True, text=True),
}

def extract_fenced_blocks(text: str) -> list:
    pattern = r'