use std::collections::hash_map::DefaultHasher;
use std::hash::{Hash, Hasher};

const RING_SIZE: usize = 256;
const BLOOM_SIZE: usize = 2048;
const HASH_FUNCS: usize = 3;

pub struct PatternDetector {
    ring: [u64; RING_SIZE],
    head: usize,
    bloom: [u64; BLOOM_SIZE / 64],
    pattern_counts: [u16; RING_SIZE],
}

impl PatternDetector {
    pub fn new() -> Self {
        Self {
            ring: [0; RING_SIZE],
            head: 0,
            bloom: [0; BLOOM_SIZE / 64],
            pattern_counts: [0; RING_SIZE],
        }
    }

    #[inline]
    fn hash(&self, s: &str, seed: usize) -> u64 {
        let mut hasher = DefaultHasher::new();
        seed.hash(&mut hasher);
        s.hash(&mut hasher);
        hasher.finish()
    }

    #[inline]
    fn bloom_set(&mut self, hash: u64) {
        let idx = (hash as usize) % BLOOM_SIZE;
        self.bloom[idx / 64] |= 1u64 << (idx % 64);
    }

    #[inline]
    fn bloom_test(&self, hash: u64) -> bool {
        let idx = (hash as usize) % BLOOM_SIZE;
        (self.bloom[idx / 64] & (1u64 << (idx % 64))) != 0
    }

    pub fn record(&mut self, pattern: &str) -> bool {
        let primary = self.hash(pattern, 0);
        let slot = (primary as usize) % RING_SIZE;
        
        let mut seen = true;
        for i in 0..HASH_FUNCS {
            let h = self.hash(pattern, i);
            if !self.bloom_test(h) {
                seen = false;
                self.bloom_set(h);
            }
        }
        
        self.ring[self.head] = primary;
        self.head = (self.head + 1) % RING_SIZE;
        
        if seen {
            self.pattern_counts[slot] = self.pattern_counts[slot].saturating_add(1);
        }
        
        seen
    }

    pub fn get_frequency(&self, pattern: &str) -> u16 {
        let primary = self.hash(pattern, 0);
        let slot = (primary as usize) % RING_SIZE;
        self.pattern_counts[slot]
    }

    pub fn detect_gaps(&self) -> Vec<usize> {
        let mut gaps = Vec::with_capacity(8);
        let avg: u32 = self.pattern_counts.iter().map(|&x| x as u32).sum::<u32>() / RING_SIZE as u32;
        
        for (i, &count) in self.pattern_counts.iter().enumerate() {
            if (count as u32) < avg / 4 {
                gaps.push(i);
            }
        }
        gaps
    }
}