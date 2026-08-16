#!/usr/bin/env python3
import re
from typing import List, Tuple

def tokenize_request(text: str) -> List[str]:
    """Split on clause boundaries: periods, 'and', 'then', semicolons."""
    text = re.sub(r'\s+', ' ', text.strip())
    delimiters = r'[.;]|\band\b|\bthen\b|\balso\b'
    return [c.strip() for c in re.split(delimiters, text) if c.strip()]

def extract_verb_object(clause: str) -> Tuple[str, str]:
    """Pull primary verb and object from clause."""
    words = clause.lower().split()
    verbs = {'build', 'create', 'extract', 'analyze', 'generate', 'validate', 
             'verify', 'identify', 'detect', 'design', 'route', 'bond', 'shape'}
    
    verb = next((w for w in words if w in verbs), words[0] if words else '')
    obj_start = words.index(verb) + 1 if verb in words else 0
    obj = ' '.join(words[obj_start:obj_start+3]) if obj_start < len(words) else ''
    
    return verb, obj

def suggest_function_name(verb: str, obj: str) -> str:
    """Generate clear, verb-first function name."""
    obj_clean = re.sub(r'[^\w\s]', '', obj).replace(' ', '_')
    return f"{verb}_{obj_clean}" if obj_clean else verb

def decompose_to_functions(request: str) -> List[dict]:
    """Main: break request into atomic function candidates."""
    clauses = tokenize_request(request)
    functions = []
    
    for clause in clauses:
        verb, obj = extract_verb_object(clause)
        if verb:
            functions.append({
                'name': suggest_function_name(verb, obj),
                'purpose': clause,
                'composable': len(clauses) > 1
            })
    
    return functions

def main():
    sample = "Build a domain vocabulary extractor that analyzes problem statements and generates specialized microlanguages before solution implementation"
    funcs = decompose_to_functions(sample)
    
    for f in funcs:
        pipe = '|' if f['composable'] else ''
        print(f"{f['name']}()  {pipe}  # {f['purpose']}")

if __name__ == '__main__':
    main()