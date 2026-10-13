#!/usr/bin/env python3
from typing import Any, Callable, Dict, List, Optional, Tuple
from dataclasses import dataclass
from inspect import signature, Parameter
import ast

@dataclass(frozen=True)
class Contract:
    preconditions: Tuple[str, ...]
    postconditions: Tuple[str, ...]
    invariants: Tuple[str, ...]

class ContractValidator:
    def __init__(self):
        self.contracts: Dict[str, Contract] = {}
        self.violations: List[str] = []
    
    def register(self, func_name: str, contract: Contract) -> None:
        assert func_name not in self.contracts, f"Contract already exists: {func_name}"
        self.contracts[func_name] = contract
    
    def validate_static(self, func_name: str, func: Callable) -> bool:
        if func_name not in self.contracts:
            return True
        
        sig = signature(func)
        contract = self.contracts[func_name]
        
        for pre in contract.preconditions:
            if not self._parse_condition(pre, sig):
                self.violations.append(f"{func_name}: precondition malformed: {pre}")
                return False
        
        for post in contract.postconditions:
            if not self._parse_condition(post, sig):
                self.violations.append(f"{func_name}: postcondition malformed: {post}")
                return False
        
        return len(self.violations) == 0
    
    def _parse_condition(self, condition: str, sig) -> bool:
        try:
            tree = ast.parse(condition, mode='eval')
            names = {node.id for node in ast.walk(tree) if isinstance(node, ast.Name)}
            param_names = set(sig.parameters.keys()) | {'result', 'self'}
            return names.issubset(param_names)
        except SyntaxError:
            return False
    
    def guard(self, func: Callable) -> Callable:
        func_name = func.__name__
        contract = self.contracts.get(func_name)
        
        if not contract:
            return func
        
        def wrapped(*args, **kwargs):
            bound = signature(func).bind(*args, **kwargs)
            bound.apply_defaults()
            scope = dict(bound.arguments)
            
            for pre in contract.preconditions:
                assert eval(pre, {}, scope), f"Precondition failed: {pre}"
            
            result = func(*args, **kwargs)
            scope['result'] = result
            
            for post in contract.postconditions:
                assert eval(post, {}, scope), f"Postcondition failed: {post}"
            
            return result
        
        return wrapped

validator = ContractValidator()