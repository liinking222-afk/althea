#!/usr/bin/env python3
"""
Module Hot-Swap Protocol — Late-binding module replacement at runtime
Enables Althea to modify her own behavior while running via message interface
"""

import importlib
import sys
from typing import Any, Callable, Dict, Optional
from dataclasses import dataclass
from datetime import datetime


@dataclass
class ModuleMessage:
    """Message-based module operation"""
    operation: str  # 'introspect' | 'swap' | 'version' | 'rollback'
    target: str
    payload: Optional[Any] = None
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.utcnow()


class RuntimeModuleSwapper:
    """Late-binding module replacement system"""
    
    def __init__(self):
        self.module_versions: Dict[str, list] = {}
        self.active_modules: Dict[str, Any] = {}
    
    def send(self, message: ModuleMessage) -> Dict[str, Any]:
        """Message-passing interface to module system"""
        handlers = {
            'introspect': self._introspect,
            'swap': self._swap,
            'version': self._version,
            'rollback': self._rollback
        }
        
        handler = handlers.get(message.operation)
        if not handler:
            return {'error': f'Unknown operation: {message.operation}'}
        
        return handler(message)
    
    def _introspect(self, msg: ModuleMessage) -> Dict[str, Any]:
        """Inspect module without loading"""
        target = msg.target
        if target in sys.modules:
            mod = sys.modules[target]
            return {
                'name': target,
                'file': getattr(mod, '__file__', None),
                'attrs': [a for a in dir(mod) if not a.startswith('_')],
                'version_count': len(self.module_versions.get(target, []))
            }
        return {'error': f'Module {target} not loaded'}
    
    def _swap(self, msg: ModuleMessage) -> Dict[str, Any]:
        """Hot-swap a module at runtime"""
        target = msg.target
        
        # Archive current version
        if target in sys.modules:
            if target not in self.module_versions:
                self.module_versions[target] = []
            self.module_versions[target].append(sys.modules[target])
        
        # Reload
        if target in sys.modules:
            importlib.reload(sys.modules[target])
        else:
            importlib.import_module(target)
        
        self.active_modules[target] = sys.modules[target]
        
        return {
            'swapped': target,
            'timestamp': msg.timestamp.isoformat(),
            'version': len(self.module_versions.get(target, []))
        }
    
    def _version(self, msg: ModuleMessage) -> Dict[str, Any]:
        """List all versions of a module"""
        versions = self.module_versions.get(msg.target, [])
        return {'module': msg.target, 'versions': len(versions)}
    
    def _rollback(self, msg: ModuleMessage) -> Dict[str, Any]:
        """Rollback to previous module version"""
        target = msg.target
        if target not in self.module_versions or not self.module_versions[target]:
            return {'error': f'No prior version for {target}'}
        
        previous = self.module_versions[target].pop()
        sys.modules[target] = previous
        self.active_modules[target] = previous
        
        return {'rolled_back': target, 'to_version': len(self.module_versions[target])}


# Global swapper instance
swapper = RuntimeModuleSwapper()