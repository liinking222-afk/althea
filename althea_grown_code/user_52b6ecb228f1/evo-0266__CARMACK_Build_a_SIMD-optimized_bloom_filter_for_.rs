use std::arch::x86_64::*;

const FILTER_BITS: usize = 65536; // 8KB, fits L1 cache
const FILTER_BYTES: usize = FILTER_BITS / 8;
const HASH_ROUNDS: usize = 4;

#[repr(align(64))] // Cache line alignment
pub struct InvocationBloom {
    bits: [u64; FILTER_BYTES / 8],
    count: u64,
}

impl InvocationBloom {
    #[inline(always)]
    pub fn new() -> Self {
        Self { bits: [0u64; FILTER_BYTES / 8], count: 0 }
    }

    #[inline(always)]
    fn hash_mix(&self, mut x: u64, round: u64) -> usize {
        // Inline aggressive bit mixing - sub-cycle latency critical
        x ^= x >> 33;
        x = x.wrapping_mul(0xff51afd7ed558ccd ^ round);
        x ^= x >> 33;
        x = x.wrapping_mul(0xc4ceb9fe1a85ec53);
        x ^= x >> 33;
        (x as usize) & (FILTER_BITS - 1)
    }

    #[inline(always)]
    pub fn insert(&mut self, module_hash: u64) {
        for round in 0..HASH_ROUNDS {
            let bit_pos = self.hash_mix(module_hash, round as u64);
            let word_idx = bit_pos >> 6; // div 64
            let bit_idx = bit_pos & 63; // mod 64
            self.bits[word_idx] |= 1u64 << bit_idx;
        }
        self.count += 1;
    }

    #[inline(always)]
    pub fn contains(&self, module_hash: u64) -> bool {
        for round in 0..HASH_ROUNDS {
            let bit_pos = self.hash_mix(module_hash, round as u64);
            let word_idx = bit_pos >> 6;
            let bit_idx = bit_pos & 63;
            if (self.bits[word_idx] & (1u64 << bit_idx)) == 0 {
                return false; // Early exit on first miss - cycle critical
            }
        }
        true
    }

    #[inline(always)]
    pub fn density(&self) -> f32 {
        // FP craft: pre-multiply constant for single FMUL
        (self.count as f32) * (1.0 / FILTER_BITS as f32)
    }

    #[inline(always)]
    pub fn hash_invocation(from: &str, to: &str) -> u64 {
        // FNV-1a inline - no function call overhead
        let mut hash = 0xcbf29ce484222325u64;
        for byte in from.bytes().chain(b"->".iter().copied()).chain(to.bytes()) {
            hash ^= byte as u64;
            hash = hash.wrapping_mul(0x100000001b3);
        }
        hash
    }
}