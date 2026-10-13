#!/usr/bin/env python3
import re
from collections import defaultdict, Counter
from typing import Dict, List, Tuple

def analyze_growth_trajectory(memory_log: str) -> Dict:
    """Analyze memory for incomplete patterns and weak execution chains."""
    
    # Extract all growth attempts
    growth_pattern = r'\[GROWTH /autonomous-([^\]]+)\]'
    autosynth_pattern = r'\[AUTOSYNTH /autonomous-([^\]]+)\]'
    evo_pattern = r'\[EVO #(\d+) \w+ v([\d.]+)→([\d.]+)\] ([^—]+)'
    
    growth_attempts = re.findall(growth_pattern, memory_log)
    autosynth_attempts = re.findall(autosynth_pattern, memory_log)
    evo_completions = re.findall(evo_pattern, memory_log)
    
    # Identify truncated entries (incomplete thoughts)
    truncation_indicators = [
        line for line in memory_log.split('\n') 
        if line.strip() and (
            line.endswith('ap') or 
            line.endswith('—') and len(line.split('—')[-1].strip()) < 10 or
            'rationale:' in line and len(line.split('rationale:')[-1].strip()) < 20
        )
    ]
    
    # Count duplicate module concepts
    all_modules = growth_attempts + [a.split('-')[0] for a in autosynth_attempts]
    module_frequency = Counter(all_modules)
    
    # Calculate completion ratio
    total_attempts = len(growth_attempts) + len(autosynth_attempts)
    completed = len(evo_completions)
    completion_rate = completed / total_attempts if total_attempts > 0 else 0
    
    # Identify weak seams (repeated but never completed)
    weak_seams = {
        module: count 
        for module, count in module_frequency.items() 
        if count > 1
    }
    
    # Extract concept themes
    theme_words = []
    for attempt in growth_attempts + autosynth_attempts:
        theme_words.extend(re.findall(r'[a-z]+', attempt.lower()))
    theme_counter = Counter(theme_words)
    
    return {
        'completion_rate': completion_rate,
        'truncations': len(truncation_indicators),
        'weak_seams': weak_seams,
        'top_incomplete_themes': theme_counter.most_common(5),
        'completion_velocity': completed / max(1, len(set([e[0] for e in evo_completions]))),
        'fragmentation_score': len(set(all_modules)) / max(1, len(all_modules)),
        'recommendation': _generate_recommendation(completion_rate, weak_seams, truncation_indicators)
    }

def _generate_recommendation(rate: float, seams: Dict, truncations: List) -> str:
    if rate < 0.3:
        return "CRITICAL: Implement completion forcing mechanism"
    elif len(truncations) > 3:
        return "HIGH: Add thought-completion buffer before context loss"
    elif seams:
        return f"MEDIUM: Prioritize completing: {list(seams.keys())[0]}"
    return "LOW: Continue current trajectory"

if __name__ == '__main__':
    import sys
    memory = sys.stdin.read() if not sys.stdin.isatty() else ""
    result = analyze_growth_trajectory(memory)
    print(f"Completion Rate: {result['completion_rate']:.2%}")
    print(f"Weak Seams: {result['weak_seams']}")
    print(f"Recommendation: {result['recommendation']}")