from typing import Callable, Dict, Any, List, Tuple
from functools import reduce
import re

class EventAlgebra:
    """Declarative event transformation through functional composition"""
    
    @staticmethod
    def identity(event: Dict[str, Any]) -> Dict[str, Any]:
        return event
    
    @staticmethod
    def compose(*transforms: Callable) -> Callable:
        """Compose transformations right-to-left (mathematical style)"""
        return lambda event: reduce(lambda e, f: f(e), reversed(transforms), event)
    
    @staticmethod
    def map_field(field: str, fn: Callable) -> Callable:
        """Pure field transformation"""
        def transform(event: Dict[str, Any]) -> Dict[str, Any]:
            if field in event:
                return {**event, field: fn(event[field])}
            return event
        return transform
    
    @staticmethod
    def filter_predicate(pred: Callable[[Dict[str, Any]], bool]) -> Callable:
        """Algebraic filter as transformation"""
        return lambda event: event if pred(event) else None
    
    @staticmethod
    def fold_pattern(pattern: str, reducer: str) -> Callable:
        """Collapse matching patterns via reduction"""
        regex = re.compile(pattern)
        def transform(event: Dict[str, Any]) -> Dict[str, Any]:
            if 'type' in event and regex.match(event['type']):
                return {**event, 'reduced': reducer, 'canonical': True}
            return event
        return transform
    
    @staticmethod
    def merge_metadata(**metadata) -> Callable:
        """Pure metadata injection"""
        return lambda event: {**event, 'meta': {**event.get('meta', {}), **metadata}}
    
    @staticmethod
    def pipeline(event: Dict[str, Any], *rules: Tuple[str, Callable]) -> Dict[str, Any]:
        """Execute declarative transformation pipeline"""
        transforms = [rule[1] for rule in rules]
        composed = EventAlgebra.compose(*transforms)
        return composed(event)

def create_deduplication_algebra() -> Callable:
    """Declarative deduplication as pure composition"""
    return EventAlgebra.compose(
        EventAlgebra.fold_pattern(r'^AUTOSYNTH.*', 'AUTOSYNTH_CLASS'),
        EventAlgebra.fold_pattern(r'^EVO.*', 'EVOLUTION_CLASS'),
        EventAlgebra.map_field('timestamp', lambda t: t // 3600 * 3600),
        EventAlgebra.merge_metadata(compressed=True, algebraic=True)
    )