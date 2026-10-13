#!/usr/bin/env python3
"""signal_stats.py - Compute basic statistics for time-series signals.
Reads JSON array from stdin, writes statistics to stdout.
"""
import sys
import json
import math


def mean(values):
    """Calculate arithmetic mean."""
    return sum(values) / len(values) if values else 0.0


def variance(values, sample_mean):
    """Calculate variance."""
    if len(values) < 2:
        return 0.0
    return sum((x - sample_mean) ** 2 for x in values) / (len(values) - 1)


def peak_to_peak(values):
    """Calculate peak-to-peak amplitude."""
    return max(values) - min(values) if values else 0.0


def zero_crossings(values):
    """Count number of times signal crosses zero."""
    if len(values) < 2:
        return 0
    count = 0
    for i in range(len(values) - 1):
        if values[i] * values[i + 1] < 0:
            count += 1
    return count


def compute_signal_stats(signal):
    """Single function: compute all basic statistics for a signal."""
    if not signal:
        return {}
    
    sample_mean = mean(signal)
    sample_variance = variance(signal, sample_mean)
    
    return {
        "count": len(signal),
        "mean": sample_mean,
        "std_dev": math.sqrt(sample_variance),
        "min": min(signal),
        "max": max(signal),
        "peak_to_peak": peak_to_peak(signal),
        "zero_crossings": zero_crossings(signal)
    }


if __name__ == "__main__":
    signal = json.load(sys.stdin)
    stats = compute_signal_stats(signal)
    json.dump(stats, sys.stdout, indent=2)
    print()