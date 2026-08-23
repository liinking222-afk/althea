use std::collections::hash_map::DefaultHasher;
use std::hash::{Hash, Hasher};

const RING_SIZE: usize = 256;
const TOMBSTONE: u64 = 0;

pub struct MemoryDedup {
    ring: [u64; RING_SIZE],
    head: usize,
}

impl MemoryDedup {
    pub fn new() -> Self {
        Self {
            ring: [TOMBSTONE; RING_SIZE],
            head: 0,
        }
    }

    #[inline]
    fn hash_bytes(data: &[u8]) -> u64 {
        let mut hasher = DefaultHasher::new();
        data.hash(&mut hasher);
        let h = hasher.finish();
        if h == TOMBSTONE { 1 } else { h }
    }

    pub fn is_duplicate(&self, pattern: &str) -> bool {
        let hash = Self::hash_bytes(pattern.as_bytes());
        self.ring.iter().any(|&h| h == hash)
    }

    pub fn record(&mut self, pattern: &str) -> bool {
        let hash = Self::hash_bytes(pattern.as_bytes());
        
        if self.is_duplicate(pattern) {
            return false;
        }
        
        self.ring[self.head] = hash;
        self.head = (self.head + 1) & (RING_SIZE - 1);
        true
    }

    pub fn clear(&mut self) {
        self.ring.fill(TOMBSTONE);
        self.head = 0;
    }

    pub fn contains(&self, pattern: &str) -> bool {
        self.is_duplicate(pattern)
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_dedup() {
        let mut dedup = MemoryDedup::new();
        assert!(dedup.record("weather-inquiry"));
        assert!(!dedup.record("weather-inquiry"));
        assert!(dedup.record("semantic-field"));
        assert!(dedup.contains("weather-inquiry"));
    }
}