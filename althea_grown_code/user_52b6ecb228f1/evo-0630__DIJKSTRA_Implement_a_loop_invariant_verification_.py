"""
loop_invariant_verifier.py
Formal verification of loop invariants with Dijkstra-style assertions.
"""

from typing import Callable, Any, Optional
from dataclasses import dataclass
from functools import wraps


@dataclass
class Invariant:
    """Encapsulates a loop invariant with its verification predicate."""
    name: str
    predicate: Callable[[Any], bool]
    
    def verify(self, state: Any) -> None:
        """Assert invariant holds; raise if violated."""
        if not self.predicate(state):
            raise AssertionError(f"Invariant '{self.name}' violated")


class VerifiedLoop:
    """Enforces pre/post/invariant conditions on iterative computation."""
    
    def __init__(self, precondition: Callable[[Any], bool],
                 postcondition: Callable[[Any], bool],
                 invariants: list[Invariant]):
        self.pre = precondition
        self.post = postcondition
        self.invariants = invariants
    
    def execute(self, initial_state: Any, 
                step: Callable[[Any], tuple[Any, bool]]) -> Any:
        """
        Execute loop with formal verification at each iteration.
        step returns (new_state, continue_flag).
        """
        # P: precondition must hold
        assert self.pre(initial_state), "Precondition violated"
        
        state = initial_state
        iteration = 0
        
        while True:
            # I: invariant must hold at loop entry
            for inv in self.invariants:
                inv.verify(state)
            
            # Execute one iteration
            state, should_continue = step(state)
            iteration += 1
            
            if not should_continue:
                break
        
        # Q: postcondition must hold at termination
        assert self.post(state), "Postcondition violated"
        
        return state


def binary_search_verified(arr: list[int], target: int) -> int:
    """Example: binary search with verified invariants."""
    
    def pre(s): 
        return s['low'] == 0 and s['high'] == len(s['arr']) - 1
    
    def post(s):
        return (s['result'] == -1 or s['arr'][s['result']] == s['target'])
    
    inv_bounds = Invariant(
        "bounds_valid",
        lambda s: 0 <= s['low'] <= s['high'] < len(s['arr'])
    )
    
    loop = VerifiedLoop(pre, post, [inv_bounds])
    
    def step(s):
        mid = (s['low'] + s['high']) // 2
        if s['arr'][mid] == s['target']:
            return {**s, 'result': mid}, False
        elif s['low'] >= s['high']:
            return {**s, 'result': -1}, False
        elif s['arr'][mid] < s['target']:
            return {**s, 'low': mid + 1}, True
        else:
            return {**s, 'high': mid - 1}, True
    
    state = {'arr': arr, 'target': target, 'low': 0, 
             'high': len(arr) - 1, 'result': -1}
    return loop.execute(state, step)['result']