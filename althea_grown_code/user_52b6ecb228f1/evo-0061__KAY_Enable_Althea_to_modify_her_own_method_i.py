#!/usr/bin/env python3
"""Runtime Method Rebinding System - Late-binding code evolution"""

import types
import inspect
from typing import Callable, Any, Dict
from datetime import datetime

class LiveObject:
    """Base class for objects that can rebind their methods at runtime"""
    
    def __init__(self):
        self._method_versions: Dict[str, list] = {}
        self._rebind_log = []
    
    def rebind_method(self, method_name: str, new_impl: Callable, reason: str = ""):
        """Replace a method implementation while the object is running"""
        if method_name not in self._method_versions:
            original = getattr(self, method_name, None)
            self._method_versions[method_name] = [original] if original else []
        
        self._method_versions[method_name].append(new_impl)
        setattr(self, method_name, types.MethodType(new_impl, self))
        
        self._rebind_log.append({
            'method': method_name,
            'timestamp': datetime.now().isoformat(),
            'reason': reason,
            'version': len(self._method_versions[method_name])
        })
        
        return self
    
    def rollback_method(self, method_name: str, versions: int = 1):
        """Revert to a previous version of a method"""
        if method_name in self._method_versions and len(self._method_versions[method_name]) > versions:
            history = self._method_versions[method_name]
            target_impl = history[-(versions + 1)]
            setattr(self, method_name, types.MethodType(target_impl, self))
            return True
        return False
    
    def get_rebind_history(self):
        """Return complete history of runtime modifications"""
        return self._rebind_log.copy()


class MessageEnvelope:
    """Encapsulate code as first-class message"""
    
    def __init__(self, code_str: str, signature: str = ""):
        self.code = code_str
        self.signature = signature
        self.compiled = None
    
    def compile_to_function(self, globals_dict: Dict = None) -> Callable:
        """Compile message payload into executable function"""
        if globals_dict is None:
            globals_dict = {}
        
        exec(self.code, globals_dict)
        func_name = self.code.split('def ')[1].split('(')[0].strip()
        self.compiled = globals_dict[func_name]
        return self.compiled
    
    def send_to(self, target: LiveObject, method_name: str, reason: str = ""):
        """Send this code message to an object, binding it as a method"""
        func = self.compile_to_function()
        target.rebind_method(method_name, func, reason)


if __name__ == "__main__":
    obj = LiveObject()
    obj.rebind_method('process', lambda self, x: x * 2, "initial")
    print(obj.process(5))
    
    msg = MessageEnvelope("def process(self, x):\n    return x ** 2")
    msg.send_to(obj, 'process', "evolution to square")
    print(obj.process(5))