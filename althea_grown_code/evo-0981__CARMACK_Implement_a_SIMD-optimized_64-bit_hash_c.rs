#![allow(overflowing_literals)]
use std::arch::x86_64::*;

#[repr(align(64))]
pub struct FastPatternHash {
    bloom: [u64; 16],  // 1024-bit bloom filter, cache-line aligned
    last: [u64; 4],    // last 4 hashes for instant duplicate check
    ring_idx: u8,
}

impl FastPatternHash {
    #[inline(always)]
    pub const fn new() -> Self {
        Self { bloom: [0u64; 16], last: [0u64; 4], ring_idx: 0 }
    }
    
    #[inline(always)]
    fn hash_combine(a: u64, b: u64) -> u64 {
        // Carmack-style: multiply-rotate-xor, maximizes avalanche
        let mut h = a.wrapping_mul(0x517cc1b727220a95);
        h = (h << 31) | (h >> 33);  // rotate 31 bits
        h ^= b.wrapping_mul(0xbf58476d1ce4e5b9);
        h = h.wrapping_mul(0x94d049bb133111eb);
        h ^ (h >> 27)
    }
    
    #[inline(always)]
    pub fn hash_pattern(&self, pattern: &str, context: &str) -> u64 {
        let mut h = 0xcbf29ce484222325u64;  // FNV offset basis
        for byte in pattern.bytes() {
            h ^= byte as u64;
            h = h.wrapping_mul(0x100000001b3);  // FNV prime
        }
        Self::hash_combine(h, context.len() as u64)
    }
    
    #[inline(always)]
    pub fn seen_recently(&self, hash: u64) -> bool {
        // HOT PATH: check last 4 with no branching, unrolled
        let eq0 = self.last[0] == hash;
        let eq1 = self.last[1] == hash;
        let eq2 = self.last[2] == hash;
        let eq3 = self.last[3] == hash;
        eq0 | eq1 | eq2 | eq3
    }
    
    #[inline(always)]
    pub fn check_bloom(&self, hash: u64) -> bool {
        // Three hash positions, branchless bit checks
        let h1 = (hash & 0x3FF) as usize;           // bits 0-9
        let h2 = ((hash >> 10) & 0x3FF) as usize;   // bits 10-19
        let h3 = ((hash >> 20) & 0x3FF) as usize;   // bits 20-29
        
        let slot1 = (self.bloom[h1 >> 6] >> (h1 & 63)) & 1;
        let slot2 = (self.bloom[h2 >> 6] >> (h2 & 63)) & 1;
        let slot3 = (self.bloom[h3 >> 6] >> (h3 & 63)) & 1;
        
        (slot1 & slot2 & slot3) == 1
    }
    
    #[inline(always)]
    pub fn insert(&mut self, hash: u64) {
        // Update ring buffer (last 4)
        self.last[self.ring_idx as usize] = hash;
        self.ring_idx = (self.ring_idx + 1) & 3;  // mod 4, branchless
        
        // Set bloom bits
        let h1 = (hash & 0x3FF) as usize;
        let h2 = ((hash >> 10) & 0x3FF) as usize;
        let h3 = ((hash >> 20) & 0x3FF) as usize;
        
        self.bloom[h1 >> 6] |= 1u64 << (h1 & 63);
        self.bloom[h2 >> 6] |= 1u64 << (h2 & 63);
        self.bloom[h3 >> 6] |= 1u64 << (h3 & 63);
    }
}