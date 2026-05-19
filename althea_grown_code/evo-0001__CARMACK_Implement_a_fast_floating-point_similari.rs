// Phase-transition detection via fast locality-sensitive hashing
// Optimized for cache-line alignment and SIMD-friendly operations
use std::arch::x86_64::*;

#[repr(align(64))]
pub struct PhaseDetector {
    ring: [f32; 64],        // Power-of-2 for bitwise wrap, cache-line aligned
    idx: usize,
    planes: [[f32; 64]; 8], // Random projection planes, pre-computed
    prev_hash: u8,
    transition_count: u32,
}

impl PhaseDetector {
    #[inline(always)]
    pub fn new(seed: u64) -> Self {
        let mut planes = [[0.0f32; 64]; 8];
        let mut rng = seed;
        for plane in &mut planes {
            for val in plane.iter_mut() {
                rng = rng.wrapping_mul(6364136223846793005).wrapping_add(1);
                *val = ((rng >> 32) as f32 / 4294967296.0) - 0.5; // Fast uniform [-0.5, 0.5]
            }
        }
        Self { ring: [0.0; 64], idx: 0, planes, prev_hash: 0, transition_count: 0 }
    }

    #[inline(always)]
    pub fn push(&mut self, signal: f32) -> Option<u32> {
        self.ring[self.idx & 63] = signal;
        self.idx = self.idx.wrapping_add(1);
        
        if self.idx & 7 != 0 { return None; } // Sample every 8th for temporal coherence
        
        // Fast LSH: dot products with random planes, threshold at 0
        let mut hash: u8 = 0;
        for (bit, plane) in self.planes.iter().enumerate() {
            let mut dot = 0.0f32;
            // Manual unroll for predictable pipeline, 8-wide accumulation
            for chunk in 0..8 {
                let base = chunk * 8;
                dot += self.ring[base] * plane[base]
                     + self.ring[base+1] * plane[base+1]
                     + self.ring[base+2] * plane[base+2]
                     + self.ring[base+3] * plane[base+3]
                     + self.ring[base+4] * plane[base+4]
                     + self.ring[base+5] * plane[base+5]
                     + self.ring[base+6] * plane[base+6]
                     + self.ring[base+7] * plane[base+7];
            }
            if dot > 0.0 { hash |= 1 << bit; }
        }
        
        // Hamming distance for phase-shift detection
        let hamming = (hash ^ self.prev_hash).count_ones();
        self.prev_hash = hash;
        
        if hamming >= 4 { // Threshold: >50% bits flipped = phase transition
            self.transition_count = self.transition_count.wrapping_add(1);
            Some(self.transition_count)
        } else {
            None
        }
    }
}