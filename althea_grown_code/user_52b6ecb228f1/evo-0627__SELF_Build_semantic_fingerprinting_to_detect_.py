import hashlib
import json
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, asdict

@dataclass
class ModuleFingerprint:
    """Semantic fingerprint of a module's capabilities"""
    capability_hash: str
    intent_hash: str
    signature: str
    first_seen: str
    instances: List[str]

class RedundancyDetector:
    """Detects when new modules duplicate existing capabilities"""
    
    def __init__(self):
        self.fingerprints: Dict[str, ModuleFingerprint] = {}
    
    def _extract_capability_signature(self, module_spec: Dict[str, Any]) -> str:
        """Extract normalized capability signature from module spec"""
        capability = module_spec.get('capability', '').lower().strip()
        domain = module_spec.get('domain', '').lower().strip()
        key_params = sorted([
            k for k in module_spec.get('parameters', {}).keys()
        ])
        return f"{domain}::{capability}::{','.join(key_params)}"
    
    def _hash_semantic_intent(self, module_spec: Dict[str, Any]) -> str:
        """Hash the semantic intent, ignoring implementation details"""
        intent_keys = ['capability', 'domain', 'input_type', 'output_type']
        intent_data = {k: module_spec.get(k) for k in intent_keys if k in module_spec}
        return hashlib.sha256(
            json.dumps(intent_data, sort_keys=True).encode()
        ).hexdigest()[:16]
    
    def check_redundancy(self, module_spec: Dict[str, Any], module_id: str) -> Optional[ModuleFingerprint]:
        """Returns existing fingerprint if module is redundant, None otherwise"""
        signature = self._extract_capability_signature(module_spec)
        intent_hash = self._hash_semantic_intent(module_spec)
        
        # Check for exact signature match
        if signature in self.fingerprints:
            fp = self.fingerprints[signature]
            fp.instances.append(module_id)
            return fp
        
        return None
    
    def register_module(self, module_spec: Dict[str, Any], module_id: str, timestamp: str):
        """Register a new unique module"""
        signature = self._extract_capability_signature(module_spec)
        intent_hash = self._hash_semantic_intent(module_spec)
        
        self.fingerprints[signature] = ModuleFingerprint(
            capability_hash=intent_hash,
            intent_hash=intent_hash,
            signature=signature,
            first_seen=timestamp,
            instances=[module_id]
        )
    
    def get_redundancy_report(self) -> Dict[str, List[str]]:
        """Return all capabilities with multiple instances"""
        return {
            fp.signature: fp.instances 
            for fp in self.fingerprints.values() 
            if len(fp.instances) > 1
        }