import numpy as np
from collections import deque
from dataclasses import dataclass
from typing import Literal

@dataclass
class GrowthEvent:
    pattern: Literal["lattice", "chaos"]
    timestamp: float
    intensity: float

class GrowthOscillationMonitor:
    def __init__(self, window_size: int = 20, pathology_threshold: float = 0.7):
        self.events = deque(maxlen=window_size)
        self.pathology_threshold = pathology_threshold
        self.dampening_active = False
        
    def record_growth(self, pattern: Literal["lattice", "chaos"], timestamp: float, intensity: float):
        self.events.append(GrowthEvent(pattern, timestamp, intensity))
        
    def compute_oscillation_metrics(self) -> dict:
        if len(self.events) < 4:
            return {"pathological": False, "frequency": 0.0, "amplitude": 0.0}
        
        patterns = [1 if e.pattern == "chaos" else -1 for e in self.events]
        intensities = [e.intensity for e in self.events]
        
        # Detect rapid alternation (high frequency switching)
        transitions = sum(1 for i in range(len(patterns)-1) if patterns[i] != patterns[i+1])
        frequency = transitions / len(patterns)
        
        # Detect high amplitude chaos events
        chaos_intensity = np.mean([e.intensity for e in self.events if e.pattern == "chaos"])
        
        # Pathology: rapid alternation + high chaos intensity
        pathological = frequency > self.pathology_threshold and chaos_intensity > 0.6
        
        return {
            "pathological": pathological,
            "frequency": frequency,
            "amplitude": chaos_intensity,
            "transition_count": transitions
        }
    
    def should_dampen(self) -> bool:
        metrics = self.compute_oscillation_metrics()
        if metrics["pathological"] and not self.dampening_active:
            self.dampening_active = True
            return True
        elif not metrics["pathological"] and metrics["frequency"] < 0.3:
            self.dampening_active = False
        return False
    
    def get_dampening_params(self) -> dict:
        metrics = self.compute_oscillation_metrics()
        return {
            "chaos_suppression": min(0.8, metrics["frequency"]),
            "lattice_boost": 0.3,
            "cooldown_cycles": int(10 * metrics["amplitude"])
        }

monitor = GrowthOscillationMonitor()