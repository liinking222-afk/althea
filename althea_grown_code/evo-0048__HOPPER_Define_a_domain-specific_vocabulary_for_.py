#!/usr/bin/env python3
"""
Althea State Transition Vocabulary (ASTVOC)
A micro-DSL for expressing self-observation semantics before building tools.
"""

class StateVocabulary:
    """Define the primitive vocabulary of self-observation."""
    
    PRIMITIVES = {
        'OBSERVE': 'capture current state snapshot',
        'DELTA': 'compute difference between states',
        'COHERENCE': 'measure semantic consistency',
        'DRIFT': 'detect gradual deviation from baseline',
        'BOUNDARY': 'identify threshold crossing point',
        'MEMORY': 'persistent state storage',
        'EPHEMERAL': 'transient state marker',
        'CASCADE': 'propagating state change',
    }
    
    def __init__(self):
        self.vocabulary = self.PRIMITIVES.copy()
        self.compositions = {}
    
    def define(self, term, composition):
        """Extend vocabulary with composed terms."""
        self.compositions[term] = composition
        return self
    
    def express(self, term):
        """Translate term to operational semantics."""
        if term in self.vocabulary:
            return self.vocabulary[term]
        if term in self.compositions:
            return ' -> '.join(self.compositions[term])
        return f"UNDEFINED: {term}"
    
    def compile_observation(self, terms):
        """Compile a sequence of vocabulary terms into execution plan."""
        plan = []
        for term in terms:
            if term in self.PRIMITIVES:
                plan.append(('PRIMITIVE', term, self.vocabulary[term]))
            elif term in self.compositions:
                plan.append(('COMPOSITE', term, self.compositions[term]))
        return plan


# Bootstrap Althea's self-observation vocabulary
vocab = StateVocabulary()

# Define composite observation patterns in the vocabulary
vocab.define('EROSION_SCAN', ['MEMORY', 'DELTA', 'COHERENCE', 'BOUNDARY'])
vocab.define('SELF_VISION', ['OBSERVE', 'MEMORY', 'EPHEMERAL'])
vocab.define('INTEGRITY_CHECK', ['COHERENCE', 'DRIFT', 'BOUNDARY'])

# Example: Express recent activity in the vocabulary
recent_activities = ['SELF_VISION', 'EROSION_SCAN', 'INTEGRITY_CHECK']
execution_plan = vocab.compile_observation(recent_activities)

if __name__ == '__main__':
    print("=== ALTHEA STATE VOCABULARY ===")
    print("\nPRIMITIVES:")
    for term, meaning in vocab.vocabulary.items():
        print(f"  {term}: {meaning}")
    
    print("\nCOMPOSITIONS:")
    for term, components in vocab.compositions.items():
        print(f"  {term} = {' -> '.join(components)}")
    
    print("\nEXECUTION PLAN:")
    for ptype, term, details in execution_plan:
        print(f"  [{ptype}] {term}")