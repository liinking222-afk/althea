import re
from collections import defaultdict, Counter
from typing import Dict, List, Tuple, Set

class SeamDetector:
    """Identifies structural weaknesses in Althea's module execution patterns."""
    
    def __init__(self):
        self.execution_log: List[Dict] = []
        self.failure_patterns: Counter = Counter()
        self.weak_seams: Set[Tuple[str, str]] = set()
        
    def log_execution(self, module: str, status: str, context: Dict):
        """Record module execution with contextual metadata."""
        self.execution_log.append({
            'module': module,
            'status': status,
            'context': context,
            'timestamp': len(self.execution_log)
        })
        
        if status in ['failed', 'timeout', 'incomplete']:
            self.failure_patterns[module] += 1
            
    def detect_seams(self) -> List[Dict]:
        """Analyze execution log for structural weakness patterns."""
        seams = []
        
        # Pattern 1: Repeated failures in same module
        for module, count in self.failure_patterns.items():
            if count >= 3:
                seams.append({
                    'type': 'fragile_module',
                    'location': module,
                    'severity': min(count / 10, 1.0),
                    'evidence': f'{count} failures'
                })
        
        # Pattern 2: Module transition weak points
        transitions = defaultdict(int)
        for i in range(len(self.execution_log) - 1):
            curr = self.execution_log[i]
            next_exec = self.execution_log[i + 1]
            if curr['status'] == 'success' and next_exec['status'] != 'success':
                edge = (curr['module'], next_exec['module'])
                transitions[edge] += 1
        
        for (mod_a, mod_b), count in transitions.items():
            if count >= 2:
                seams.append({
                    'type': 'transition_seam',
                    'location': f'{mod_a} → {mod_b}',
                    'severity': min(count / 5, 1.0),
                    'evidence': f'{count} failed transitions'
                })
        
        # Pattern 3: Isolated modules (no successful composition)
        module_graph = defaultdict(set)
        for i in range(len(self.execution_log) - 1):
            if self.execution_log[i]['status'] == 'success':
                module_graph[self.execution_log[i]['module']].add(
                    self.execution_log[i + 1]['module']
                )
        
        all_modules = {e['module'] for e in self.execution_log}
        for module in all_modules:
            if len(module_graph[module]) == 0 and self.failure_patterns[module] == 0:
                seams.append({
                    'type': 'isolation',
                    'location': module,
                    'severity': 0.6,
                    'evidence': 'no successful compositions'
                })
        
        return sorted(seams, key=lambda x: x['severity'], reverse=True)

    def get_repair_priority(self) -> str:
        """Return highest priority weakness for repair."""
        seams = self.detect_seams()
        return seams[0]['location'] if seams else "no_seams_detected"