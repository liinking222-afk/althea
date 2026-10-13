import re
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass

@dataclass
class CapabilityRequest:
    domain: str
    action: str
    parameters: Dict[str, str]
    confidence: float

class ConversationPatternCompiler:
    """Hopper-style compiler: conversation → capability vocabulary"""
    
    def __init__(self):
        self.vocabulary = {
            'visualization': {
                'patterns': [r'(?:show|plot|graph|chart|visualize)\s+(.+)',
                            r'(?:make|create|draw)\s+a\s+(?:chart|graph|plot)'],
                'domain': 'data-visualization',
                'action': 'render'
            },
            'lookup': {
                'patterns': [r'(?:what|tell me|find)\s+(?:is|about)\s+(.+)',
                            r'properties of\s+(.+)',
                            r'(?:chemistry|chemical|element|molecule):\s*(.+)'],
                'domain': 'knowledge-retrieval',
                'action': 'fetch'
            },
            'computation': {
                'patterns': [r'(?:calculate|compute|solve)\s+(.+)',
                            r'how (?:much|many|tall|long|far)\s+(?:is|are)\s+(.+)'],
                'domain': 'computation',
                'action': 'evaluate'
            },
            'analysis': {
                'patterns': [r'analyze\s+(.+)',
                            r'(?:compare|contrast)\s+(.+)\s+(?:and|with|vs)\s+(.+)',
                            r'semantic\s+(?:gap|void|missing)'],
                'domain': 'semantic-analysis',
                'action': 'process'
            }
        }
    
    def compile(self, utterance: str) -> List[CapabilityRequest]:
        """Compile natural language into capability requests"""
        requests = []
        utterance_lower = utterance.lower().strip()
        
        for capability, spec in self.vocabulary.items():
            for pattern in spec['patterns']:
                match = re.search(pattern, utterance_lower)
                if match:
                    params = {f'arg{i}': g for i, g in enumerate(match.groups())}
                    confidence = 0.9 if len(match.group(0)) / len(utterance_lower) > 0.4 else 0.6
                    
                    requests.append(CapabilityRequest(
                        domain=spec['domain'],
                        action=spec['action'],
                        parameters=params,
                        confidence=confidence
                    ))
        
        return sorted(requests, key=lambda r: r.confidence, reverse=True)
    
    def define_capability(self, name: str, patterns: List[str], domain: str, action: str):
        """Extend the vocabulary dynamically"""
        self.vocabulary[name] = {
            'patterns': patterns,
            'domain': domain,
            'action': action
        }
    
    def to_formal_request(self, request: CapabilityRequest) -> str:
        """Generate formal module invocation syntax"""
        params = ','.join(f'{k}={v}' for k, v in request.parameters.items())
        return f"[INVOKE /{request.domain} {request.action}({params})]"

# Example usage
compiler = ConversationPatternCompiler()