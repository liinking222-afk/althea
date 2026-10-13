#!/usr/bin/env python3
import sys
import json
from datetime import datetime

def parse_timestamp(ts):
    try:
        if isinstance(ts, (int, float)):
            return datetime.fromtimestamp(ts)
        return datetime.fromisoformat(ts.replace('Z', '+00:00'))
    except:
        return None

def summarize_memory(record):
    try:
        data = json.loads(record) if isinstance(record, str) else record
        
        ts = parse_timestamp(data.get('timestamp', ''))
        ts_str = ts.strftime('%Y-%m-%d %H:%M:%S') if ts else 'UNKNOWN'
        
        mem_type = data.get('type', 'UNKNOWN')
        content = data.get('content', data.get('pattern', ''))
        
        if isinstance(content, dict):
            content = content.get('description', str(content)[:60])
        
        content_preview = str(content)[:70].replace('\n', ' ')
        
        confidence = data.get('confidence', data.get('activation', 0))
        conf_bar = '█' * int(confidence * 10) + '░' * (10 - int(confidence * 10))
        
        return f"{ts_str} | {mem_type:12} | {conf_bar} | {content_preview}"
    except Exception as e:
        return f"PARSE_ERROR | {str(e)[:60]} | {record[:50]}"

def main():
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        print(summarize_memory(line))
        sys.stdout.flush()

if __name__ == '__main__':
    main()