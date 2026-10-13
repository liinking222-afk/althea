use std::arch::x86_64::*;

const CACHE_LINE: usize = 64;
const PATTERN_SLOTS: usize = 8;

#[repr(align(64))]
pub struct VectorPatternMatcher {
    patterns: [[u64; 8]; PATTERN_SLOTS], // 64B aligned, 8x u64 per pattern
    masks: [u64; PATTERN_SLOTS],          // bit-parallel activation masks
    scores: [f32; PATTERN_SLOTS],         // hot-cache score array
}

impl VectorPatternMatcher {
    #[inline(always)]
    pub fn new() -> Self {
        Self {
            patterns: [[0u64; 8]; PATTERN_SLOTS],
            masks: [0u64; PATTERN_SLOTS],
            scores: [0.0f32; PATTERN_SLOTS],
        }
    }

    // Hash token sequence into 8x u64 SIMD-friendly chunks
    #[inline(always)]
    fn hash_sequence(&self, tokens: &[u64]) -> [u64; 8] {
        let mut hashes = [0u64; 8];
        let len = tokens.len().min(64);
        for i in 0..len {
            hashes[i >> 3] ^= tokens[i].rotate_left(((i & 7) * 8) as u32);
        }
        hashes
    }

    // Branchless parallel match across all patterns
    #[inline(always)]
    pub fn match_parallel(&mut self, tokens: &[u64]) -> u8 {
        let query = self.hash_sequence(tokens);
        let mut result = 0u8;
        
        // Unrolled hot loop - compiler will vectorize
        for slot in 0..PATTERN_SLOTS {
            let mut match_bits = 0u64;
            
            // XOR-popcount distance metric (Hamming)
            for lane in 0..8 {
                match_bits |= (query[lane] ^ self.patterns[slot][lane]).count_ones() as u64;
            }
            
            // Branchless: distance < threshold activates bit
            let threshold = 24u64; // tunable: ~3 bits per lane
            let matched = ((threshold.wrapping_sub(match_bits)) >> 63) ^ 1;
            result |= (matched as u8) << slot;
            
            // Hot-path score update: fused multiply-add
            self.scores[slot] = self.scores[slot].mul_add(0.95, matched as f32 * 0.05);
        }
        
        result
    }

    // Install pattern with cache-friendly sequential write
    #[inline(always)]
    pub fn install_pattern(&mut self, slot: usize, tokens: &[u64]) {
        if slot < PATTERN_SLOTS {
            self.patterns[slot] = self.hash_sequence(tokens);
            self.masks[slot] = !0u64; // full mask
            self.scores[slot] = 0.0;
        }
    }

    // Return top-k active patterns without allocation
    #[inline(always)]
    pub fn top_active(&self, k: usize) -> [usize; PATTERN_SLOTS] {
        let mut indices = [0usize; PATTERN_SLOTS];
        for i in 0..PATTERN_SLOTS { indices[i] = i; }
        
        // Branchless insertion sort on scores (k always small)
        for i in 1..PATTERN_SLOTS.min(k * 2) {
            let mut j = i;
            while j > 0 && self.scores[indices[j]] > self.scores[indices[j-1]] {
                indices.swap(j, j-1);
                j -= 1;
            }
        }
        indices
    }
}