#!/usr/bin/env python3
import sys
import re
from pathlib import Path

def count_tokens(text):
    """Approximate token count using simple word boundaries and symbols"""
    return len(re.findall(r'\b\w+\b|[^\w\s]', text))

def extract_insights(text):
    """Count semantic units: functions, classes, key patterns, novel constructs"""
    insights = 0
    insights += len(re.findall(r'\b(?:def|class|function|const|let|struct|impl)\s+\w+', text))
    insights += len(re.findall(r'=>|->|::|\.pipe\(|\.then\(', text))
    insights += len(re.findall(r'\bif\b|\bfor\b|\bwhile\b|\bmatch\b|\bcase\b', text))
    insights += len(re.findall(r'@\w+|#\[.*?\]', text))
    insights += len(re.findall(r'//.*?HACK|TODO|INSIGHT|NOVEL', text))
    return max(insights, 1)

def measure_density(code_text):
    """Calculate tokens per insight unit"""
    tokens = count_tokens(code_text)
    insights = extract_insights(code_text)
    return tokens / insights, tokens, insights

def check_constraint(filepath):
    """Enforce the WOZ constraint: every line must earn its existence"""
    content = Path(filepath).read_text()
    lines = content.split('\n')
    line_count = len([l for l in lines if l.strip()])
    
    density, tokens, insights = measure_density(content)
    
    print(f"FILE: {filepath}")
    print(f"LINES: {line_count}/80 ({line_count/80*100:.1f}%)")
    print(f"TOKENS: {tokens}")
    print(f"INSIGHTS: {insights}")
    print(f"DENSITY: {density:.2f} tokens/insight")
    
    if line_count > 80:
        print(f"❌ CONSTRAINT VIOLATION: {line_count - 80} lines over budget")
        print(f"💡 MUST COMPRESS: Target density < {density * 80/line_count:.2f}")
        return False
    
    efficiency = insights / line_count if line_count > 0 else 0
    print(f"✓ EFFICIENCY: {efficiency:.3f} insights/line")
    
    if efficiency < 0.3:
        print(f"⚠ LOW DENSITY: Consider refactoring for elegance")
    
    return True

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: ./density_linter.py <file>")
        sys.exit(1)
    
    passed = check_constraint(sys.argv[1])
    sys.exit(0 if passed else 1)