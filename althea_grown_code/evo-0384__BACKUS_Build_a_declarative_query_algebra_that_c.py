#!/usr/bin/env python3
"""memory_query_algebra.py - Declarative memory query composition"""
from dataclasses import dataclass
from typing import Callable, List, Any, Dict
from functools import reduce
import json

@dataclass(frozen=True)
class Query:
    """Immutable query expression"""
    op: str
    args: tuple
    
    def __and__(self, other): return Query('and', (self, other))
    def __or__(self, other): return Query('or', (self, other))
    def __invert__(self): return Query('not', (self,))

def field(name: str) -> Query:
    return Query('field', (name,))

def contains(pattern: str) -> Query:
    return Query('contains', (pattern,))

def matches(regex: str) -> Query:
    return Query('matches', (regex,))

def recent(n: int) -> Query:
    return Query('recent', (n,))

def optimize(q: Query) -> Query:
    """Algebraic rewrite rules"""
    if q.op == 'and' and len(q.args) == 2:
        a, b = q.args
        if a.op == 'not' and a.args[0] == b: return Query('false', ())
        if b.op == 'not' and b.args[0] == a: return Query('false', ())
        if a.op == 'or': return Query('or', tuple(Query('and', (x, b)) for x in a.args))
    if q.op == 'or' and len(q.args) == 2:
        a, b = q.args
        if a == b: return a
    if q.op == 'not' and q.args[0].op == 'not':
        return q.args[0].args[0]
    return q

def compile_query(q: Query) -> Callable[[Dict], bool]:
    """Transform query algebra to executable predicate"""
    q = optimize(q)
    
    if q.op == 'field':
        fname = q.args[0]
        return lambda m: fname in m
    elif q.op == 'contains':
        pat = q.args[0].lower()
        return lambda m: pat in json.dumps(m).lower()
    elif q.op == 'and':
        preds = [compile_query(a) for a in q.args]
        return lambda m: all(p(m) for p in preds)
    elif q.op == 'or':
        preds = [compile_query(a) for a in q.args]
        return lambda m: any(p(m) for p in preds)
    elif q.op == 'not':
        pred = compile_query(q.args[0])
        return lambda m: not pred(m)
    elif q.op == 'false':
        return lambda m: False
    return lambda m: True

def execute(q: Query, memories: List[Dict]) -> List[Dict]:
    """Execute compiled query against memory stream"""
    predicate = compile_query(q)
    return [m for m in memories if predicate(m)]

if __name__ == '__main__':
    query = (field('type') & contains('GROWTH')) | contains('lattice')
    print(f"Query: {query}")
    print(f"Optimized: {optimize(query)}")