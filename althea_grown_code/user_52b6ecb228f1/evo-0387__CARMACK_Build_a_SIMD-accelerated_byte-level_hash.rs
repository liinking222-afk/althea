use std::arch::x86_64::*;
use std::collections::HashMap;

const BLOCK_SIZE: usize = 64; // Cache line aligned
const FNV_PRIME: u64 = 0x100000001b3;
const FNV_OFFSET: u64 = 0xcbf29ce484222325;

#[repr(align(64))]
struct Block([u8; BLOCK_SIZE]);

pub struct DedupIndex {
    fingerprints: HashMap<u64, Vec<usize>>, // hash -> block indices
    block_count: usize,
}

impl DedupIndex {
    #[inline(always)]
    pub fn new() -> Self {
        Self { fingerprints: HashMap::with_capacity(4096), block_count: 0 }
    }

    // Hot path: FNV-1a with manual unroll for ILP
    #[inline(always)]
    unsafe fn hash_block_fnv(data: &[u8; BLOCK_SIZE]) -> u64 {
        let mut h = FNV_OFFSET;
        let mut i = 0;
        
        // Unroll by 8 for instruction-level parallelism
        while i + 8 <= BLOCK_SIZE {
            h = (h ^ data[i] as u64).wrapping_mul(FNV_PRIME);
            h = (h ^ data[i+1] as u64).wrapping_mul(FNV_PRIME);
            h = (h ^ data[i+2] as u64).wrapping_mul(FNV_PRIME);
            h = (h ^ data[i+3] as u64).wrapping_mul(FNV_PRIME);
            h = (h ^ data[i+4] as u64).wrapping_mul(FNV_PRIME);
            h = (h ^ data[i+5] as u64).wrapping_mul(FNV_PRIME);
            h = (h ^ data[i+6] as u64).wrapping_mul(FNV_PRIME);
            h = (h ^ data[i+7] as u64).wrapping_mul(FNV_PRIME);
            i += 8;
        }
        
        while i < BLOCK_SIZE {
            h = (h ^ data[i] as u64).wrapping_mul(FNV_PRIME);
            i += 1;
        }
        h
    }

    #[inline]
    pub fn index_bytes(&mut self, data: &[u8]) -> Vec<(usize, Option<usize>)> {
        let mut results = Vec::with_capacity(data.len() / BLOCK_SIZE);
        let chunks = data.chunks_exact(BLOCK_SIZE);
        
        for (idx, chunk) in chunks.enumerate() {
            let mut block = [0u8; BLOCK_SIZE];
            block.copy_from_slice(chunk);
            
            let hash = unsafe { Self::hash_block_fnv(&block) };
            
            let duplicate = self.fingerprints
                .get(&hash)
                .and_then(|v| v.first().copied());
            
            self.fingerprints.entry(hash).or_insert_with(Vec::new).push(idx);
            results.push((idx, duplicate));
            self.block_count += 1;
        }
        results
    }

    #[inline]
    pub fn dedup_ratio(&self) -> f64 {
        let unique = self.fingerprints.len();
        if self.block_count == 0 { return 1.0; }
        unique as f64 / self.block_count as f64
    }
}