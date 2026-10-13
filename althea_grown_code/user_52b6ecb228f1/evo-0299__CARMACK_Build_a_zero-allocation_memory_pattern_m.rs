const MAX_PATTERNS: usize = 256;
const PATTERN_BITS: usize = 64;
const HASH_PRIME: u64 = 0x517cc1b727220a95;

#[repr(align(64))]
struct PatternCache {
    signatures: [u64; MAX_PATTERNS],
    frequencies: [u32; MAX_PATTERNS],
    last_seen: [u32; MAX_PATTERNS],
    tick: u32,
}

impl PatternCache {
    #[inline(always)]
    fn new() -> Self {
        Self {
            signatures: [0; MAX_PATTERNS],
            frequencies: [0; MAX_PATTERNS],
            last_seen: [0; MAX_PATTERNS],
            tick: 0,
        }
    }

    #[inline(always)]
    fn hash_concept(&self, tokens: &[&str]) -> u64 {
        let mut h = HASH_PRIME;
        for &token in tokens {
            for byte in token.bytes() {
                h = h.rotate_left(5) ^ (byte as u64);
                h = h.wrapping_mul(HASH_PRIME);
            }
        }
        h
    }

    #[inline(always)]
    fn record(&mut self, concept: &[&str]) -> (u8, u32, bool) {
        self.tick = self.tick.wrapping_add(1);
        let sig = self.hash_concept(concept);
        let slot = (sig as usize) & (MAX_PATTERNS - 1);
        
        // Fast path: exact match in expected slot
        if self.signatures[slot] == sig {
            let freq = self.frequencies[slot].saturating_add(1);
            self.frequencies[slot] = freq;
            let recency = self.tick - self.last_seen[slot];
            self.last_seen[slot] = self.tick;
            return (slot as u8, freq, recency < 10);
        }
        
        // Probe linear, max 8 steps (cache-friendly)
        for probe in 1..8 {
            let idx = (slot + probe) & (MAX_PATTERNS - 1);
            if self.signatures[idx] == sig || self.signatures[idx] == 0 {
                self.signatures[idx] = sig;
                let freq = self.frequencies[idx].saturating_add(1);
                self.frequencies[idx] = freq;
                let was_recent = self.last_seen[idx] > 0 && (self.tick - self.last_seen[idx]) < 10;
                self.last_seen[idx] = self.tick;
                return (idx as u8, freq, was_recent);
            }
        }
        
        (0, 0, false) // Miss
    }
}

static mut CACHE: PatternCache = PatternCache {
    signatures: [0; MAX_PATTERNS],
    frequencies: [0; MAX_PATTERNS],
    last_seen: [0; MAX_PATTERNS],
    tick: 0,
};