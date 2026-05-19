// ===============================
// QUANTUM MIND OS - LIVE NEURAL BRAIN
// FULL EMERGENT INTEGRATION BUILD
// ===============================

// -------------------------------
// QUANTUM STATE ENGINE
// -------------------------------
export class QuantumState {
    constructor(states = []) {
        this.states = states;
    }

    observe() {
        return this.states.map((s) => s.value);
    }

    collapse() {
        let total = this.states.reduce((a, b) => a + b.weight, 0);
        let r = Math.random() * total;

        for (let s of this.states) {
            r -= s.weight;
            if (r <= 0) return s.value;
        }
    }
}

// -------------------------------
// LIVE NEURAL MEMORY LATTICE
// -------------------------------
export class MemoryLattice {
    constructor() {
        this.nodes = new Map();
        this.activity = new Map(); // live brain firing timestamps
    }

    store(key, value) {
        if (!this.nodes.has(key)) {
            this.nodes.set(key, {
                value,
                links: new Set(),
                strength: 1,
            });
        } else {
            const node = this.nodes.get(key);
            node.value = value;
            node.strength += 0.15;
        }

        // LIVE ACTIVITY SIGNAL (for visualization pulse)
        this.activity.set(key, Date.now());
    }

    entangle(a, b) {
        if (!this.nodes.has(a)) this.store(a, null);
        if (!this.nodes.has(b)) this.store(b, null);

        this.nodes.get(a).links.add(b);
        this.nodes.get(b).links.add(a);
    }

    // Neural signal propagation (brain-like spreading activation)
    propagate(seed) {
        const node = this.nodes.get(seed);
        if (!node) return;

        for (let link of node.links) {
            const linked = this.nodes.get(link);
            if (linked) {
                linked.strength += 0.02;
            }
        }
    }

    recall(key) {
        const node = this.nodes.get(key);
        if (!node) return [];

        return {
            value: node.value,
            linked: Array.from(node.links),
        };
    }

    // -------------------------------
    // LIVE BRAIN VISUALIZATION EXPORT
    // -------------------------------
    exportGraph() {
        const nodes = [];
        const edges = [];

        for (let [key, node] of this.nodes.entries()) {
            nodes.push({
                id: key,
                label: String(node.value || key),

                // LIVE BRAIN SIGNALS
                activity: this.activity.get(key) || 0,
                strength: node.strength,

                // UI VISUAL METRICS
                size: 1 + node.strength * 0.5,
            });

            for (let link of node.links) {
                edges.push({
                    from: key,
                    to: link,
                    weight: node.strength,
                });
            }
        }

        return {
            nodes,
            edges,
            updated: Date.now(),
        };
    }
}

// -------------------------------
// MULTI-AGENT COGNITIVE SYSTEM
// (SIMULATED INTERNAL THINKING LAYERS)
// -------------------------------
async function plannerAgent(input) {
    return `PLAN LAYER:
Break task into structured steps for: "${input}"`;
}

async function reasonerAgent(input, memory) {
    return `REASON LAYER:
Analyze input: "${input}"
Memory Context: ${JSON.stringify(memory)}`;
}

async function criticAgent(output) {
    return `CRITIC LAYER:
Evaluate and refine:
${output}`;
}

// -------------------------------
// QUANTUM DECISION ENGINE
// -------------------------------
export function quantumFuse(outputs) {
    return new QuantumState(
        outputs.map((o) => ({
            value: o,
            weight: Math.random(),
        })),
    ).collapse();
}

// -------------------------------
// CORE QUANTUM MIND OS KERNEL
// -------------------------------
export class QuantumMindOS {
    constructor() {
        this.memory = new MemoryLattice();
        this._subs = new Set();
    }

    // pub/sub so React components can react to live brain updates
    subscribe(fn) {
        this._subs.add(fn);
        return () => this._subs.delete(fn);
    }

    _emit() {
        for (const fn of this._subs) {
            try {
                fn(this.memory.exportGraph());
            } catch (_) {
                /* ignore subscriber errors */
            }
        }
    }

    async process(input) {
        // -------------------------------
        // MEMORY + BRAIN PROPAGATION
        // -------------------------------
        const memoryContext = this.memory.recall(input);
        this.memory.propagate(input);

        // -------------------------------
        // MULTI-AGENT THINKING LOOP
        // -------------------------------
        const plan = await plannerAgent(input);
        const reasoning = await reasonerAgent(input, memoryContext);
        const critique = await criticAgent(reasoning);

        // -------------------------------
        // QUANTUM SUPERPOSITION LAYER
        // -------------------------------
        const quantum = new QuantumState([
            { value: plan, weight: 0.2 },
            { value: reasoning, weight: 0.5 },
            { value: critique, weight: 0.3 },
        ]);

        const collapsed = quantum.collapse();

        // -------------------------------
        // MEMORY STORAGE + ENTANGLEMENT
        // -------------------------------
        this.memory.store(input, collapsed);
        this.memory.entangle(input, "core_node");

        // notify visualisers
        this._emit();

        // -------------------------------
        // RETURN LIVE BRAIN STATE
        // -------------------------------
        return {
            input,

            // cognitive layers
            superposition: quantum.observe(),
            collapsed,

            // memory snapshot
            memory: this.memory.recall(input),

            // LIVE BRAIN VISUALIZATION FEED (IMPORTANT)
            brain: this.memory.exportGraph(),
        };
    }

    reset() {
        this.memory = new MemoryLattice();
        this._emit();
    }

    snapshot() {
        return this.memory.exportGraph();
    }
}

// -------------------------------
// EMERGENT ENTRY POINT (STATEFUL)
// -------------------------------
const os = new QuantumMindOS();

export async function runQuantumOS(userInput) {
    if (userInput.startsWith("/status")) {
        return "Quantum Mind OS - LIVE NEURAL BRAIN ACTIVE";
    }

    return await os.process(userInput);
}

export const quantumOS = os;
