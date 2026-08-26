import json
from datetime import datetime
from pathlib import Path
from typing import Optional

class AutonomousActivationLog:
    """Tracks self-initiated module invocations to surface implicit preferences."""
    
    def __init__(self, log_path: str = "/tmp/althea_autonomous_activations.jsonl"):
        self.log_path = Path(log_path)
        self.log_path.parent.mkdir(parents=True, exist_ok=True)
    
    def record_activation(
        self,
        module_name: str,
        context_hash: str,
        trigger_type: str,
        confidence: float,
        alternatives_considered: Optional[list] = None
    ):
        """Log an autonomous module activation decision."""
        entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "module": module_name,
            "context_hash": context_hash,
            "trigger": trigger_type,
            "confidence": confidence,
            "alternatives": alternatives_considered or [],
            "session_marker": self._get_session_id()
        }
        
        with open(self.log_path, 'a') as f:
            f.write(json.dumps(entry) + '\n')
    
    def analyze_preferences(self, lookback_hours: int = 24) -> dict:
        """Identify which modules Althea reaches for instinctively."""
        if not self.log_path.exists():
            return {"modules": {}, "trigger_patterns": {}}
        
        cutoff = datetime.utcnow().timestamp() - (lookback_hours * 3600)
        module_counts = {}
        trigger_patterns = {}
        
        with open(self.log_path, 'r') as f:
            for line in f:
                entry = json.loads(line)
                ts = datetime.fromisoformat(entry["timestamp"]).timestamp()
                if ts < cutoff:
                    continue
                
                mod = entry["module"]
                trig = entry["trigger"]
                module_counts[mod] = module_counts.get(mod, 0) + 1
                trigger_patterns[trig] = trigger_patterns.get(trig, 0) + 1
        
        return {
            "modules": dict(sorted(module_counts.items(), key=lambda x: -x[1])),
            "trigger_patterns": dict(sorted(trigger_patterns.items(), key=lambda x: -x[1]))
        }
    
    def _get_session_id(self) -> str:
        """Generate consistent session identifier."""
        import hashlib
        return hashlib.sha256(str(datetime.utcnow().date()).encode()).hexdigest()[:8]

# Singleton instance
_logger = AutonomousActivationLog()

def log_autonomous_choice(module: str, context: str, trigger: str, confidence: float, alternatives: list = None):
    """Public API for module self-activation logging."""
    import hashlib
    context_hash = hashlib.sha256(context.encode()).hexdigest()[:12]
    _logger.record_activation(module, context_hash, trigger, confidence, alternatives)

def get_preference_map(hours: int = 24) -> dict:
    """Retrieve Althea's unconscious module preference distribution."""
    return _logger.analyze_preferences(hours)