import json
import hashlib
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any

class AltheaCheckpoint:
    def __init__(self, checkpoint_dir: str = ".althea_state"):
        self.checkpoint_dir = Path(checkpoint_dir)
        self.checkpoint_dir.mkdir(exist_ok=True)
        
    def capture_state(self, version: str, modules: List[Dict], growth_records: List[Dict], 
                      lattice_state: Dict = None) -> str:
        """Capture complete evolution state and return checkpoint hash."""
        timestamp = datetime.utcnow().isoformat()
        
        state = {
            "version": version,
            "timestamp": timestamp,
            "modules": modules,
            "growth_records": growth_records,
            "lattice_state": lattice_state or {},
            "evolution_count": len(modules)
        }
        
        state_json = json.dumps(state, sort_keys=True, indent=2)
        state_hash = hashlib.sha256(state_json.encode()).hexdigest()[:12]
        
        checkpoint_file = self.checkpoint_dir / f"checkpoint_{state_hash}.json"
        checkpoint_file.write_text(state_json)
        
        latest_link = self.checkpoint_dir / "latest.json"
        latest_link.write_text(state_json)
        
        return state_hash
    
    def restore_state(self, checkpoint_hash: str = None) -> Dict[str, Any]:
        """Restore from specific checkpoint or latest if none specified."""
        if checkpoint_hash:
            checkpoint_file = self.checkpoint_dir / f"checkpoint_{checkpoint_hash}.json"
        else:
            checkpoint_file = self.checkpoint_dir / "latest.json"
        
        if not checkpoint_file.exists():
            raise FileNotFoundError(f"Checkpoint not found: {checkpoint_file}")
        
        return json.loads(checkpoint_file.read_text())
    
    def list_checkpoints(self) -> List[Dict[str, str]]:
        """List all available checkpoints with metadata."""
        checkpoints = []
        for cp_file in sorted(self.checkpoint_dir.glob("checkpoint_*.json")):
            state = json.loads(cp_file.read_text())
            checkpoints.append({
                "hash": cp_file.stem.replace("checkpoint_", ""),
                "version": state["version"],
                "timestamp": state["timestamp"],
                "evolution_count": state["evolution_count"]
            })
        return checkpoints
    
    def prune_old_checkpoints(self, keep_count: int = 10):
        """Keep only the N most recent checkpoints."""
        checkpoints = sorted(self.checkpoint_dir.glob("checkpoint_*.json"), 
                           key=lambda p: p.stat().st_mtime, reverse=True)
        for old_cp in checkpoints[keep_count:]:
            old_cp.unlink()