use std::collections::hash_map::DefaultHasher;
use std::hash::{Hash, Hasher};

const CACHE_SIZE: usize = 256; // Power of 2 for mask optimization
const EMPTY: u64 = u64::MAX;

#[repr(C)] // Cache-line friendly layout
pub struct CompositionCache {
    keys: [u64; CACHE_SIZE],   // 2KB - fits in L1
    valid: [u8; CACHE_SIZE],   // 256B - composition validity
    cost: [u16; CACHE_SIZE],   // 512B - cycle estimates
}

impl CompositionCache {
    #[inline(always)]
    pub fn new() -> Self {
        Self {
            keys: [EMPTY; CACHE_SIZE],
            valid: [0; CACHE_SIZE],
            cost: [0; CACHE_SIZE],
        }
    }

    #[inline(always)]
    fn hash_pair(left: u32, right: u32) -> u64 {
        // Szudzik pairing: zero-alloc bijection
        let (a, b) = (left as u64, right as u64);
        if a >= b { a * a + a + b } else { b * b + a }
    }

    #[inline(always)]
    pub fn check(&self, left_id: u32, right_id: u32) -> Option<(bool, u16)> {
        let hash = Self::hash_pair(left_id, right_id);
        let mut idx = (hash as usize) & (CACHE_SIZE - 1); // Mask instead of modulo
        
        // Linear probe max 4 steps - predictable branches
        for _ in 0..4 {
            let key = unsafe { *self.keys.get_unchecked(idx) };
            if key == hash {
                let valid = unsafe { *self.valid.get_unchecked(idx) };
                let cost = unsafe { *self.cost.get_unchecked(idx) };
                return Some((valid != 0, cost));
            }
            if key == EMPTY { return None; }
            idx = (idx + 1) & (CACHE_SIZE - 1);
        }
        None
    }

    #[inline(always)]
    pub fn insert(&mut self, left_id: u32, right_id: u32, is_valid: bool, cycles: u16) {
        let hash = Self::hash_pair(left_id, right_id);
        let mut idx = (hash as usize) & (CACHE_SIZE - 1);
        
        for _ in 0..4 {
            let key = unsafe { self.keys.get_unchecked_mut(idx) };
            if *key == EMPTY || *key == hash {
                *key = hash;
                self.valid[idx] = is_valid as u8;
                self.cost[idx] = cycles;
                return;
            }
            idx = (idx + 1) & (CACHE_SIZE - 1);
        }
        // Evict at probe limit - oldest entry approximation
        self.keys[idx] = hash;
        self.valid[idx] = is_valid as u8;
        self.cost[idx] = cycles;
    }
}