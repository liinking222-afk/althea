#!/usr/bin/env python3
import re
import sys
from pathlib import Path
from typing import Dict, List, Tuple, Set

def extract_signature(code: str, module_name: str) -> Dict:
    """Pure function: code -> signature algebra"""
    inputs = set()
    outputs = set()
    transforms = []
    
    # Extract input patterns (stdin, args, env, files read)
    if re.search(r'sys\.stdin|input\(|argparse|sys\.argv', code):
        inputs.add('Stream[Text]')
    if re.search(r'open\([^)]+["\']r', code):
        inputs.add('File[Read]')
    if re.search(r'json\.load|yaml\.load', code):
        inputs.add('Data[Structured]')
    if re.search(r'requests\.|urllib|httpx', code):
        inputs.add('Network[HTTP]')
    
    # Extract output patterns (stdout, files written, return)
    if re.search(r'print\(|sys\.stdout', code):
        outputs.add('Stream[Text]')
    if re.search(r'open\([^)]+["\']w', code):
        outputs.add('File[Write]')
    if re.search(r'json\.dump|yaml\.dump', code):
        outputs.add('Data[Structured]')
    if re.search(r'return .+', code):
        outputs.add('Value[Computed]')
    
    # Extract transformations (map, filter, reduce, sort)
    if re.search(r'\bmap\(|\.map\(|list comprehension', code):
        transforms.append('map')
    if re.search(r'\bfilter\(|\.filter\(|\bif\b.*\bfor\b', code):
        transforms.append('filter')
    if re.search(r'reduce\(|sum\(|\.count\(|aggregate', code):
        transforms.append('reduce')
    if re.search(r'sorted\(|\.sort\(', code):
        transforms.append('sort')
    
    # Derive algebraic signature
    in_type = ' × '.join(sorted(inputs)) if inputs else '()'
    out_type = ' + '.join(sorted(outputs)) if outputs else '()'
    composition = ' ∘ '.join(transforms) if transforms else 'id'
    
    return {
        'module': module_name,
        'signature': f"{in_type} → {out_type}",
        'composition': composition,
        'composable': len(inputs) <= 2 and len(outputs) == 1,
        'pure': 'File[Write]' not in outputs and 'Network' not in inputs
    }

def format_signature(sig: Dict) -> str:
    """Render signature as algebraic notation"""
    purity = "⊕" if sig['pure'] else "⊗"
    comp = "∘" if sig['composable'] else "×"
    return f"{sig['module']} :: {sig['signature']} [{sig['composition']}] {purity}{comp}"

if __name__ == '__main__':
    code = sys.stdin.read()
    module = sys.argv[1] if len(sys.argv) > 1 else 'anonymous'
    sig = extract_signature(code, module)
    print(format_signature(sig))