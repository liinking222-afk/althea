import re
from typing import List, Dict

def extract_function_signatures(code: str, language: str = "python") -> List[Dict[str, str]]:
    """Extract function signatures from code block."""
    patterns = {
        "python": r"def\s+(\w+)\s*\([^)]*\)\s*(?:->.*?)?:",
        "javascript": r"(?:function\s+(\w+)|const\s+(\w+)\s*=\s*(?:async\s*)?\([^)]*\)\s*=>)",
        "typescript": r"(?:function\s+(\w+)|const\s+(\w+)\s*=\s*(?:async\s*)?\([^)]*\)\s*=>)",
        "rust": r"fn\s+(\w+)\s*\([^)]*\)",
        "go": r"func\s+(?:\([^)]*\)\s*)?(\w+)\s*\([^)]*\)",
    }
    
    pattern = patterns.get(language, patterns["python"])
    matches = re.finditer(pattern, code)
    
    functions = []
    for match in matches:
        name = next((g for g in match.groups() if g), "")
        functions.append({"name": name, "language": language})
    
    return functions

def count_verbs_in_name(function_name: str) -> int:
    """Count verb-like tokens in a function name (underscores or camelCase)."""
    tokens = re.split(r'_|(?=[A-Z])', function_name.lower())
    verb_indicators = ['get', 'set', 'create', 'delete', 'update', 'fetch', 'parse', 
                       'validate', 'extract', 'compute', 'render', 'check', 'find',
                       'scan', 'load', 'save', 'transform', 'map', 'filter', 'reduce']
    return sum(1 for token in tokens if token in verb_indicators)

def assess_single_purpose(functions: List[Dict[str, str]]) -> Dict[str, any]:
    """Assess if function names suggest single-purpose design."""
    results = []
    for func in functions:
        verb_count = count_verbs_in_name(func["name"])
        word_count = len(re.split(r'_|(?=[A-Z])', func["name"]))
        
        single_purpose = verb_count <= 1 and word_count <= 4
        
        results.append({
            "name": func["name"],
            "verb_count": verb_count,
            "word_count": word_count,
            "single_purpose": single_purpose
        })
    
    clarity_score = sum(1 for r in results if r["single_purpose"]) / len(results) if results else 1.0
    
    return {
        "functions": results,
        "clarity_score": clarity_score,
        "total": len(results)
    }