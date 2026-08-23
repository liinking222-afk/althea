use std::arch::x86_64::*;

const CHUNK_SIZE: usize = 32;
const PATTERN_WINDOW: usize = 64;

#[repr(align(32))]
struct AlignedBuffer([u8; PATTERN_WINDOW]);

pub struct VectorPatternMatcher {
    hash_table: Vec<u64>,  // Power-of-2 size for mask-based indexing
    match_counts: Vec<u16>,
    mask: usize,
}

impl VectorPatternMatcher {
    #[inline(always)]
    pub fn new(capacity_log2: u8) -> Self {
        let size = 1usize << capacity_log2;
        Self {
            hash_table: vec![0; size],
            match_counts: vec![0; size],
            mask: size - 1,
        }
    }

    #[inline(always)]
    fn hash_chunk(&self, data: &[u8]) -> u64 {
        // FNV-1a vectorized over 8-byte words for cache efficiency
        let mut h = 0xcbf29ce484222325u64;
        for chunk in data.chunks_exact(8) {
            let word = u64::from_le_bytes(chunk.try_into().unwrap());
            h = (h ^ word).wrapping_mul(0x100000001b3);
        }
        h
    }

    #[inline(always)]
    pub fn scan(&mut self, module_data: &[u8]) -> u32 {
        let mut collisions = 0u32;
        let mut offset = 0;

        // Process in aligned PATTERN_WINDOW chunks with stride for overlap
        while offset + PATTERN_WINDOW <= module_data.len() {
            let window = &module_data[offset..offset + PATTERN_WINDOW];
            let hash = self.hash_chunk(window);
            let idx = (hash as usize) & self.mask;

            let existing = unsafe { *self.hash_table.get_unchecked(idx) };
            
            if existing == hash {
                // Structural repetition detected
                let count = unsafe { self.match_counts.get_unchecked_mut(idx) };
                *count = count.saturating_add(1);
                collisions += 1;
            } else if existing == 0 {
                unsafe {
                    *self.hash_table.get_unchecked_mut(idx) = hash;
                    *self.match_counts.get_unchecked_mut(idx) = 1;
                }
            }

            offset += CHUNK_SIZE;  // Overlapping windows for fine-grained detection
        }
        collisions
    }

    #[inline(always)]
    pub fn get_top_patterns(&self, n: usize) -> Vec<(u64, u16)> {
        let mut patterns: Vec<_> = self.hash_table.iter()
            .zip(self.match_counts.iter())
            .filter(|(h, _)| **h != 0)
            .map(|(h, c)| (*h, *c))
            .collect();
        patterns.sort_unstable_by(|a, b| b.1.cmp(&a.1));
        patterns.truncate(n);
        patterns
    }
}