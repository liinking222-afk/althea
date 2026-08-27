import json
from datetime import datetime, timedelta
from collections import defaultdict, Counter
from pathlib import Path

def analyze_autosynth_patterns(memory_log, threshold=3, window_hours=24):
    """
    Detects repeated AUTOSYNTH patterns that should become permanent modules.
    Returns synthesis recommendations ranked by urgency.
    """
    pattern_timeline = defaultdict(list)
    
    for entry in memory_log:
        if entry.get('type') == 'AUTOSYNTH':
            pattern_name = entry.get('pattern')
            timestamp = entry.get('timestamp', datetime.now())
            pattern_timeline[pattern_name].append(timestamp)
    
    recommendations = []
    now = datetime.now()
    cutoff = now - timedelta(hours=window_hours)
    
    for pattern, timestamps in pattern_timeline.items():
        recent = [ts for ts in timestamps if ts > cutoff]
        if len(recent) >= threshold:
            urgency = len(recent) / threshold
            recommendations.append({
                'pattern': pattern,
                'frequency': len(recent),
                'urgency': urgency,
                'first_seen': min(timestamps),
                'last_seen': max(timestamps),
                'status': 'INTERNALIZE_NOW' if urgency >= 2 else 'MONITOR'
            })
    
    recommendations.sort(key=lambda x: x['urgency'], reverse=True)
    return recommendations

def detect_synthesis_need(memory_stream):
    """Main entry point: scan memory and flag patterns for permanent integration."""
    patterns = analyze_autosynth_patterns(memory_stream)
    
    synthesis_queue = [p for p in patterns if p['status'] == 'INTERNALIZE_NOW']
    
    return {
        'timestamp': datetime.now().isoformat(),
        'synthesis_queue': synthesis_queue,
        'monitoring': [p for p in patterns if p['status'] == 'MONITOR'],
        'action_required': len(synthesis_queue) > 0
    }

if __name__ == '__main__':
    result = detect_synthesis_need([])
    print(json.dumps(result, indent=2, default=str))