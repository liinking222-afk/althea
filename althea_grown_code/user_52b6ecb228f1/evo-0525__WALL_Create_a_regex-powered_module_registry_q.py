import re
import json
from typing import List, Dict, Any, Callable

def parse_registry_query(query: str, modules: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Query module registry with flexible regex patterns and operators.
    Syntax: 
      /pattern/          - regex match on any field
      field:/pattern/    - regex on specific field
      +term              - must contain (AND)
      -term              - must not contain (NOT)
      term1|term2        - either term (OR)
      term1 term2        - both terms (implicit AND)
    """
    
    def match_module(mod: Dict[str, Any], pattern: str) -> bool:
        searchable = json.dumps(mod).lower()
        return bool(re.search(pattern.lower(), searchable))
    
    def match_field(mod: Dict[str, Any], field: str, pattern: str) -> bool:
        value = str(mod.get(field, "")).lower()
        return bool(re.search(pattern.lower(), value))
    
    # Parse query into operations
    results = modules.copy()
    
    # Handle field-specific queries: field:/pattern/
    for field_query in re.finditer(r'(\w+):/((?:[^/]|\\/)+)/', query):
        field, pattern = field_query.groups()
        results = [m for m in results if match_field(m, field, pattern)]
    
    # Remove field queries for general parsing
    clean_query = re.sub(r'\w+:/(?:[^/]|\\/)+/', '', query)
    
    # Handle general regex: /pattern/
    for regex_match in re.finditer(r'/((?:[^/]|\\/)+)/', clean_query):
        pattern = regex_match.group(1)
        results = [m for m in results if match_module(m, pattern)]
    
    # Remove regex patterns
    clean_query = re.sub(r'/(?:[^/]|\\/)+/', '', clean_query)
    
    # Handle +required terms
    for required in re.finditer(r'\+(\S+)', clean_query):
        term = required.group(1)
        results = [m for m in results if match_module(m, term)]
    
    # Handle -excluded terms
    for excluded in re.finditer(r'-(\S+)', clean_query):
        term = excluded.group(1)
        results = [m for m in results if not match_module(m, term)]
    
    # Handle OR groups: term1|term2
    or_groups = re.findall(r'(?<![+\-])(\S+\|\S+(?:\|\S+)*)', clean_query)
    for or_group in or_groups:
        terms = or_group.split('|')
        results = [m for m in results if any(match_module(m, t) for t in terms)]
    
    return results

# Example usage / self-test
if __name__ == "__main__":
    test_modules = [
        {"name": "chemistry-lookup", "tags": ["science", "data"], "lang": "python"},
        {"name": "spectral-analysis", "tags": ["signals", "math"], "lang": "python"},
        {"name": "data-viz", "tags": ["plotting", "matplotlib"], "lang": "python"},
    ]
    
    print(parse_registry_query("lang:/python/ +science", test_modules))