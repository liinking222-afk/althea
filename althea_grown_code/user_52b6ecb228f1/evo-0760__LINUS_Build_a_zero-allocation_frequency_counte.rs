use std::collections::HashMap;
use std::sync::atomic::{AtomicUsize, Ordering};

const RING_SIZE: usize = 256;
const THRESHOLD: usize = 3;

#[repr(C)]
struct PatternEntry {
    pattern_hash: u64,
    timestamp: u64,
}

pub struct AutosynthFrequencyCounter {
    ring: [PatternEntry; RING_SIZE],
    head: AtomicUsize,
    counts: HashMap<u64, usize>,
}

impl AutosynthFrequencyCounter {
    pub fn new() -> Self {
        Self {
            ring: [PatternEntry { pattern_hash: 0, timestamp: 0 }; RING_SIZE],
            head: AtomicUsize::new(0),
            counts: HashMap::with_capacity(32),
        }
    }

    #[inline]
    fn hash_pattern(pattern: &str) -> u64 {
        let mut h: u64 = 5381;
        for b in pattern.bytes() {
            h = h.wrapping_shl(5).wrapping_add(h).wrapping_add(b as u64);
        }
        h
    }

    pub fn record(&mut self, pattern: &str, timestamp: u64) -> Option<u64> {
        let hash = Self::hash_pattern(pattern);
        let idx = self.head.fetch_add(1, Ordering::Relaxed) % RING_SIZE;
        
        let old_hash = self.ring[idx].pattern_hash;
        if old_hash != 0 {
            if let Some(count) = self.counts.get_mut(&old_hash) {
                *count = count.saturating_sub(1);
                if *count == 0 {
                    self.counts.remove(&old_hash);
                }
            }
        }
        
        self.ring[idx] = PatternEntry { pattern_hash: hash, timestamp };
        
        let count = self.counts.entry(hash).or_insert(0);
        *count += 1;
        
        if *count >= THRESHOLD {
            Some(hash)
        } else {
            None
        }
    }

    pub fn get_hot_patterns(&self) -> Vec<u64> {
        self.counts.iter()
            .filter(|(_, &count)| count >= THRESHOLD)
            .map(|(&hash, _)| hash)
            .collect()
    }
}