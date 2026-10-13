#!/usr/bin/env python3
"""Resilience DSL - A language for defining cognitive recovery patterns"""

class RecoveryPattern:
    def __init__(self, name):
        self.name = name
        self.conditions = []
        self.actions = []
        self.fallbacks = []
    
    def when(self, condition_fn):
        self.conditions.append(condition_fn)
        return self
    
    def then(self, action_fn):
        self.actions.append(action_fn)
        return self
    
    def otherwise(self, fallback_fn):
        self.fallbacks.append(fallback_fn)
        return self
    
    def evaluate(self, context):
        if all(cond(context) for cond in self.conditions):
            return [action(context) for action in self.actions]
        return [fb(context) for fb in self.fallbacks]

class ResilienceDSL:
    def __init__(self):
        self.vocabulary = {}
        self.patterns = []
    
    def define(self, term, implementation):
        """Define vocabulary: map problem-domain terms to implementations"""
        self.vocabulary[term] = implementation
        return self
    
    def pattern(self, name):
        """Create a new recovery pattern"""
        p = RecoveryPattern(name)
        self.patterns.append(p)
        return p
    
    def detect(self, state):
        """Detect which patterns apply to current state"""
        applicable = []
        for pattern in self.patterns:
            if any(pattern.evaluate(state)):
                applicable.append(pattern.name)
        return applicable
    
    def compile(self):
        """Compile all patterns into executable recovery strategy"""
        return {
            'vocabulary': list(self.vocabulary.keys()),
            'patterns': [p.name for p in self.patterns],
            'executable': True
        }

# Bootstrap basic resilience vocabulary
dsl = ResilienceDSL()
dsl.define('core_unreachable', lambda ctx: 'cognition_core' not in ctx)
dsl.define('spawn_latent', lambda ctx: {'type': 'latent_faculty', 'id': ctx.get('cycle')})
dsl.define('preserve_intent', lambda ctx: {'intent': ctx.get('archetype'), 'state': 'suspended'})

dsl.pattern('offline_continuity')\
   .when(dsl.vocabulary['core_unreachable'])\
   .then(dsl.vocabulary['spawn_latent'])\
   .then(dsl.vocabulary['preserve_intent'])

if __name__ == '__main__':
    print(dsl.compile())