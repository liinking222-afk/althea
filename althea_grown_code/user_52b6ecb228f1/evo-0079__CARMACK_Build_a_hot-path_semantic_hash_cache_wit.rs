use std::hash::{Hash, Hasher};
use std::collections::hash_map::DefaultHasher;

const CACHE_SIZE: usize = 4096; // Power of 2 for mask-based indexing
const PROBE_LIMIT: u8 = 16; // Linear probe bound

#[repr(C, packed)]
struct CacheEntry {
    hash: u64,        // 8 bytes - full hash for collision check
    pattern_id: u32,  // 4 bytes - compact pattern reference
    epoch: u16,       // 2 bytes - timestamp for LRU
    probe_depth: u8,  // 1 byte - insertion cost metric
    occupied: u8,     // 1 byte - 0=empty, 1=occupied (bool packing)
}

pub struct SemanticHashCache {
    entries: Vec<CacheEntry>,
    epoch_counter: u16,
    hit_count: u32,
    miss_count: u32,
}

impl SemanticHashCache {
    #[inline(always)]
    pub fn new() -> Self {
        Self {
            entries: vec![CacheEntry { hash: 0, pattern_id: 0, epoch: 0, probe_depth: 0, occupied: 0 }; CACHE_SIZE],
            epoch_counter: 0,
            hit_count: 0,
            miss_count: 0,
        }
    }

    #[inline(always)]
    fn compute_hash(&self, semantic_text: &str) -> u64 {
        let mut hasher = DefaultHasher::new();
        semantic_text.hash(&mut hasher);
        hasher.finish()
    }

    #[inline(always)]
    pub fn lookup(&mut self, semantic_text: &str) -> Option<u32> {
        let hash = self.compute_hash(semantic_text);
        let mut idx = (hash as usize) & (CACHE_SIZE - 1); // Fast modulo
        
        for probe in 0..PROBE_LIMIT {
            let entry = unsafe { self.entries.get_unchecked(idx) }; // Bounds check eliminated
            
            if entry.occupied == 0 {
                self.miss_count += 1;
                return None; // Empty slot = definitely not cached
            }
            
            if entry.hash == hash {
                self.hit_count += 1;
                return Some(entry.pattern_id); // Cache hit
            }
            
            idx = (idx + 1) & (CACHE_SIZE - 1); // Linear probe, wraparound
        }
        
        self.miss_count += 1;
        None // Probe limit exceeded
    }

    #[inline(always)]
    pub fn insert(&mut self, semantic_text: &str, pattern_id: u32) {
        let hash = self.compute_hash(semantic_text);
        let mut idx = (hash as usize) & (CACHE_SIZE - 1);
        
        self.epoch_counter = self.epoch_counter.wrapping_add(1);
        
        for probe in 0..PROBE_LIMIT {
            let entry = unsafe { self.entries.get_unchecked_mut(idx) };
            
            if entry.occupied == 0 || entry.epoch < self.epoch_counter.wrapping_sub(256) {
                *entry = CacheEntry { hash, pattern_id, epoch: self.epoch_counter, probe_depth: probe, occupied: 1 };
                return;
            }
            
            idx = (idx + 1) & (CACHE_SIZE - 1);
        }
    }
}