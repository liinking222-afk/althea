#!/usr/bin/env python3
import re
from typing import Dict, List, Optional

class PolyglotModuleNameLinter:
    """Larry Wall lens: there's more than one way to name it, but ONE purpose only."""
    
    VAGUE_WORDS = r'\b(handle|process|manage|do|execute|perform|run|misc|util|helper|common)\b'
    CONJUNCTIONS = r'\b(and|or|with|plus|also)\b'
    
    NAMING_PATTERNS = {
        'snake_case': r'^[a-z][a-z0-9]*(_[a-z0-9]+)*$',
        'kebab-case': r'^[a-z][a-z0-9]*(-[a-z0-9]+)*$',
        'camelCase': r'^[a-z][a-zA-Z0-9]*$',
        'PascalCase': r'^[A-Z][a-zA-Z0-9]*$'
    }
    
    def __init__(self, allow_styles: List[str] = None):
        self.allow_styles = allow_styles or ['snake_case', 'kebab-case']
    
    def lint(self, name: str) -> Dict:
        """Duck-typed validation: multiple paths to clarity."""
        issues = []
        style_match = None
        
        for style in self.allow_styles:
            if re.match(self.NAMING_PATTERNS[style], name):
                style_match = style
                break
        
        if not style_match:
            issues.append(f"No matching style in {self.allow_styles}")
        
        normalized = re.sub(r'[-_]', ' ', name.lower())
        
        if re.search(self.VAGUE_WORDS, normalized, re.IGNORECASE):
            issues.append("Contains vague words (handle/process/manage/util/etc)")
        
        if re.search(self.CONJUNCTIONS, normalized, re.IGNORECASE):
            issues.append("Contains conjunction suggesting multiple purposes")
        
        verbs = re.findall(r'\b(get|set|validate|parse|render|filter|map|reduce|'
                          r'cache|route|lint|check|extract|build|load|save)\b', 
                          normalized, re.IGNORECASE)
        
        if len(verbs) > 1:
            issues.append(f"Multiple verbs detected: {verbs} - split into modules")
        elif len(verbs) == 0:
            issues.append("No clear action verb - what does this DO?")
        
        return {
            'name': name,
            'valid': len(issues) == 0,
            'style': style_match,
            'issues': issues,
            'verb_count': len(verbs)
        }

if __name__ == '__main__':
    linter = PolyglotModuleNameLinter(allow_styles=['snake_case', 'kebab-case', 'camelCase'])
    
    tests = ['validate_module_name', 'handleAndProcess', 'parse-json', 'utilCommon', 
             'extractPurpose', 'get_and_set_value']
    
    for test in tests:
        result = linter.lint(test)
        print(f"{test}: {'✓' if result['valid'] else '✗'} {result.get('issues', [])}")