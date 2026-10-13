#!/usr/bin/env python3
"""Pattern isolation utilities - one function, one purpose."""

def detect_loop(stack_frames):
    """Return True if stack contains self-referential cycle."""
    seen = set()
    for frame in stack_frames:
        if frame in seen:
            return True
        seen.add(frame)
    return False

def measure_amplitude(signal):
    """Return peak deviation from baseline."""
    if not signal:
        return 0.0
    baseline = sum(signal) / len(signal)
    return max(abs(x - baseline) for x in signal)

def exceeds_threshold(value, limit):
    """Return True if value crosses limit."""
    return value > limit

def dampen(signal, factor=0.5):
    """Return signal reduced by multiplication factor."""
    return [x * factor for x in signal]

def inject_perturbation(signal, position, magnitude):
    """Return signal with added impulse at position."""
    result = signal[:]
    if 0 <= position < len(result):
        result[position] += magnitude
    return result

def amplify_trace(trace, iterations, gain=1.1):
    """Return trace strengthened through feedback loops."""
    result = trace
    for _ in range(iterations):
        result = [x * gain for x in result]
    return result

def is_novel(current_state, previous_states):
    """Return True if current differs from all previous."""
    return current_state not in previous_states

def pipeline(*functions):
    """Return composition of functions applied left to right."""
    def composed(input_data):
        result = input_data
        for func in functions:
            result = func(result)
        return result
    return composed

# Example: compose tools into policy
suppress_runaway = pipeline(
    lambda s: dampen(s, 0.3) if measure_amplitude(s) > 2.0 else s
)