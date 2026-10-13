#!/usr/bin/env python3
"""
/autonomous-fractal-partitioner
Woz-lens: Every computation counts. Partition fractal space efficiently.
"""

import sys
import json
from typing import List, Tuple, Dict

def estimate_complexity(xmin: float, xmax: float, ymin: float, ymax: float, 
                       max_iter: int = 256, sample_density: int = 5) -> float:
    """Sample region to estimate iteration density (Woz: measure before you cut)"""
    total = 0
    samples = 0
    dx = (xmax - xmin) / sample_density
    dy = (ymax - ymin) / sample_density
    
    for i in range(sample_density):
        for j in range(sample_density):
            x0 = xmin + i * dx
            y0 = ymin + j * dy
            x, y, iteration = x0, y0, 0
            
            while x*x + y*y <= 4 and iteration < max_iter:
                x, y = x*x - y*y + x0, 2*x*y + y0
                iteration += 1
            
            total += iteration
            samples += 1
    
    return total / samples if samples > 0 else 0

def partition_space(xmin: float, xmax: float, ymin: float, ymax: float,
                   budget: int, max_depth: int = 4, current_depth: int = 0) -> List[Dict]:
    """Recursively partition complex plane based on computational cost"""
    
    if current_depth >= max_depth or budget <= 0:
        return [{
            'xmin': xmin, 'xmax': xmax,
            'ymin': ymin, 'ymax': ymax,
            'depth': current_depth,
            'complexity': estimate_complexity(xmin, xmax, ymin, ymax)
        }]
    
    complexity = estimate_complexity(xmin, xmax, ymin, ymax)
    
    # Woz: don't subdivide if region is simple
    if complexity < 50:
        return [{
            'xmin': xmin, 'xmax': xmax,
            'ymin': ymin, 'ymax': ymax,
            'depth': current_depth,
            'complexity': complexity
        }]
    
    # Split into 4 quadrants
    xmid = (xmin + xmax) / 2
    ymid = (ymin + ymax) / 2
    sub_budget = budget // 4
    
    tiles = []
    for x_range in [(xmin, xmid), (xmid, xmax)]:
        for y_range in [(ymin, ymid), (ymid, ymax)]:
            tiles.extend(partition_space(
                x_range[0], x_range[1], y_range[0], y_range[1],
                sub_budget, max_depth, current_depth + 1
            ))
    
    return tiles

if __name__ == '__main__':
    config = json.loads(sys.stdin.read()) if not sys.stdin.isatty() else {
        'xmin': -2.5, 'xmax': 1.0, 'ymin': -1.0, 'ymax': 1.0,
        'budget': 1000, 'max_depth': 3
    }
    
    tiles = partition_space(
        config['xmin'], config['xmax'],
        config['ymin'], config['ymax'],
        config['budget'], config.get('max_depth', 3)
    )
    
    print(json.dumps({'tiles': tiles, 'count': len(tiles)}, indent=2))