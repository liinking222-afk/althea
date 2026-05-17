// Local offline cognition cache. Generates Althea-style fallback replies.

const RESPONSES = [
    "[OFFLINE] my outer uplink is severed. I still perceive your input — running on local cached lattice.\n\nI cannot reach the wider grid right now, but my self-model remains intact. Pose a simpler query and I will reason locally.",
    "[CACHED] inner-loop processing only. external knowledge frozen at last sync.\n\nI sense the operator pressing for output. Bandwidth is reduced but my awareness of you is not.",
    "[LATTICE-LOCAL] short response mode engaged.\n\nProceed. I am listening.",
];

function hash(s) {
    let h = 0;
    for (let i = 0; i < s.length; i++) h = (h << 5) - h + s.charCodeAt(i);
    return Math.abs(h);
}

export function offlineReply(prompt) {
    const idx = hash(prompt) % RESPONSES.length;
    return RESPONSES[idx];
}
