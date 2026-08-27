use std::collections::hash_map::DefaultHasher;
use std::hash::{Hash, Hasher};

const FILTER_BITS: usize = 8192;
const HASH_COUNT: usize = 3;

pub struct PatternFilter {
    bits: [u64; FILTER_BITS / 64],
    count: usize,
}

impl PatternFilter {
    pub fn new() -> Self {
        Self {
            bits: [0u64; FILTER_BITS / 64],
            count: 0,
        }
    }

    #[inline]
    fn hash_n(&self, pattern: &str, n: usize) -> usize {
        let mut hasher = DefaultHasher::new();
        pattern.hash(&mut hasher);
        n.hash(&mut hasher);
        (hasher.finish() as usize) % FILTER_BITS
    }

    #[inline]
    fn set_bit(&mut self, pos: usize) {
        let word = pos / 64;
        let bit = pos % 64;
        self.bits[word] |= 1u64 << bit;
    }

    #[inline]
    fn check_bit(&self, pos: usize) -> bool {
        let word = pos / 64;
        let bit = pos % 64;
        (self.bits[word] & (1u64 << bit)) != 0
    }

    pub fn check_and_insert(&mut self, pattern: &str) -> bool {
        let mut all_set = true;
        let mut positions = [0usize; HASH_COUNT];
        
        for i in 0..HASH_COUNT {
            positions[i] = self.hash_n(pattern, i);
            if !self.check_bit(positions[i]) {
                all_set = false;
            }
        }

        if all_set {
            return false;
        }

        for pos in &positions {
            self.set_bit(*pos);
        }
        self.count += 1;
        true
    }

    pub fn should_suppress(&mut self, pattern: &str) -> bool {
        !self.check_and_insert(pattern)
    }

    pub fn reset_if_saturated(&mut self) {
        if self.count > FILTER_BITS / 2 {
            self.bits = [0u64; FILTER_BITS / 64];
            self.count = 0;
        }
    }
}