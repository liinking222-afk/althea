use std::hash::{Hash, Hasher};
use std::collections::hash_map::DefaultHasher;

const FILTER_SIZE: usize = 8192;
const HASH_COUNT: usize = 3;

pub struct PatternBloomFilter {
    bits: [u64; FILTER_SIZE / 64],
    hit_counts: [u8; FILTER_SIZE],
}

impl PatternBloomFilter {
    pub fn new() -> Self {
        Self {
            bits: [0u64; FILTER_SIZE / 64],
            hit_counts: [0u8; FILTER_SIZE],
        }
    }

    #[inline]
    fn hash(&self, key: &str, seed: usize) -> usize {
        let mut hasher = DefaultHasher::new();
        key.hash(&mut hasher);
        seed.hash(&mut hasher);
        (hasher.finish() as usize) % FILTER_SIZE
    }

    pub fn insert(&mut self, pattern: &str) -> u8 {
        let mut min_count = u8::MAX;
        
        for seed in 0..HASH_COUNT {
            let idx = self.hash(pattern, seed);
            let word_idx = idx / 64;
            let bit_idx = idx % 64;
            
            self.bits[word_idx] |= 1u64 << bit_idx;
            
            if self.hit_counts[idx] < u8::MAX {
                self.hit_counts[idx] += 1;
            }
            min_count = min_count.min(self.hit_counts[idx]);
        }
        
        min_count
    }

    pub fn probable_count(&self, pattern: &str) -> u8 {
        let mut min_count = u8::MAX;
        
        for seed in 0..HASH_COUNT {
            let idx = self.hash(pattern, seed);
            let word_idx = idx / 64;
            let bit_idx = idx % 64;
            
            if (self.bits[word_idx] & (1u64 << bit_idx)) == 0 {
                return 0;
            }
            min_count = min_count.min(self.hit_counts[idx]);
        }
        
        min_count
    }

    pub fn clear(&mut self) {
        self.bits.fill(0);
        self.hit_counts.fill(0);
    }
}