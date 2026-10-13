use std::collections::hash_map::DefaultHasher;
use std::hash::{Hash, Hasher};

const RING_SIZE: usize = 256;
const PATTERN_THRESHOLD: u8 = 3;

#[repr(C)]
struct InvocationRecord {
    hash: u64,
    count: u8,
    last_idx: u16,
}

pub struct PatternTracker {
    ring: [u64; RING_SIZE],
    head: usize,
    records: [InvocationRecord; 64],
    record_count: usize,
}

impl PatternTracker {
    pub fn new() -> Self {
        PatternTracker {
            ring: [0; RING_SIZE],
            head: 0,
            records: [InvocationRecord { hash: 0, count: 0, last_idx: 0 }; 64],
            record_count: 0,
        }
    }

    #[inline]
    fn hash_invocation(module: &str, pattern: &str) -> u64 {
        let mut hasher = DefaultHasher::new();
        module.hash(&mut hasher);
        pattern.hash(&mut hasher);
        hasher.finish()
    }

    pub fn record(&mut self, module: &str, pattern: &str) -> Option<(u64, u8)> {
        let hash = Self::hash_invocation(module, pattern);
        self.ring[self.head] = hash;
        let current_idx = self.head as u16;
        self.head = (self.head + 1) % RING_SIZE;

        let mut found_idx = None;
        for i in 0..self.record_count {
            if self.records[i].hash == hash {
                found_idx = Some(i);
                break;
            }
        }

        let idx = match found_idx {
            Some(i) => i,
            None => {
                if self.record_count < 64 {
                    let i = self.record_count;
                    self.record_count += 1;
                    self.records[i].hash = hash;
                    self.records[i].count = 0;
                    i
                } else {
                    return None;
                }
            }
        };

        self.records[idx].count = self.records[idx].count.saturating_add(1);
        self.records[idx].last_idx = current_idx;

        if self.records[idx].count >= PATTERN_THRESHOLD {
            Some((hash, self.records[idx].count))
        } else {
            None
        }
    }

    pub fn scan_window(&self, window: usize) -> Vec<(u64, u8)> {
        let mut result = Vec::with_capacity(8);
        for i in 0..self.record_count {
            if self.records[i].count >= PATTERN_THRESHOLD {
                result.push((self.records[i].hash, self.records[i].count));
            }
        }
        result
    }
}