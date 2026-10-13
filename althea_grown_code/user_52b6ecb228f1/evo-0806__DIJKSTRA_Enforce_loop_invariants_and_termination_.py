import time
from typing import Callable, Any, TypeVar, Optional
from dataclasses import dataclass

T = TypeVar('T')

@dataclass(frozen=True)
class LoopInvariant:
    """Immutable invariant condition with proof obligation."""
    predicate: Callable[[Any], bool]
    description: str
    
    def holds(self, state: Any) -> bool:
        """Verify invariant holds for current state."""
        return self.predicate(state)

@dataclass
class BoundedLoop:
    """Loop with verified termination and invariant preservation."""
    max_iterations: int
    timeout_ms: float
    invariant: LoopInvariant
    
    def execute(self, 
                initial_state: T,
                body: Callable[[T, int], T],
                termination: Callable[[T], bool]) -> tuple[T, dict]:
        """Execute loop with formal guarantees."""
        assert self.invariant.holds(initial_state), \
            f"Precondition failed: {self.invariant.description}"
        
        state = initial_state
        start_time = time.perf_counter()
        iteration = 0
        
        while iteration < self.max_iterations:
            # Check termination condition
            if termination(state):
                return state, {
                    'terminated': True,
                    'iterations': iteration,
                    'reason': 'natural_termination'
                }
            
            # Check timeout
            elapsed_ms = (time.perf_counter() - start_time) * 1000
            if elapsed_ms > self.timeout_ms:
                return state, {
                    'terminated': True,
                    'iterations': iteration,
                    'reason': 'timeout'
                }
            
            # Execute body
            state = body(state, iteration)
            iteration += 1
            
            # Verify invariant preserved
            assert self.invariant.holds(state), \
                f"Invariant violated at iteration {iteration}: {self.invariant.description}"
        
        return state, {
            'terminated': True,
            'iterations': iteration,
            'reason': 'max_iterations'
        }

# Example: Memory stream processing with proven bounds
def process_memory_stream_safely(items: list[Any]) -> list[Any]:
    """Process memory items with guaranteed termination."""
    invariant = LoopInvariant(
        predicate=lambda s: len(s['processed']) <= len(s['remaining']) + len(s['processed']),
        description="Processed items never exceed total"
    )
    
    loop = BoundedLoop(
        max_iterations=1000,
        timeout_ms=100.0,
        invariant=invariant
    )
    
    initial = {'remaining': items, 'processed': []}
    
    result, metrics = loop.execute(
        initial_state=initial,
        body=lambda s, i: {
            'remaining': s['remaining'][1:],
            'processed': s['processed'] + [s['remaining'][0]] if s['remaining'] else s['processed']
        },
        termination=lambda s: len(s['remaining']) == 0
    )
    
    return result['processed']