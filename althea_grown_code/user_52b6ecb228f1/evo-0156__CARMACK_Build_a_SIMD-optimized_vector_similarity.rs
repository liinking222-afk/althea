use std::arch::x86_64::*;

const CACHE_SIZE: usize = 64; // Power of 2 for mask optimization
const VEC_DIM: usize = 384; // Typical embedding dimension, divisible by 8

#[repr(align(32))]
struct AlignedVec([f32; VEC_DIM]);

struct HotPathCache {
    vectors: [AlignedVec; CACHE_SIZE],
    scores: [f32; CACHE_SIZE],
    hits: [u32; CACHE_SIZE],
    mask: usize,
}

impl HotPathCache {
    #[inline(always)]
    fn new() -> Self {
        Self {
            vectors: unsafe { std::mem::zeroed() },
            scores: [0.0; CACHE_SIZE],
            hits: [0; CACHE_SIZE],
            mask: CACHE_SIZE - 1,
        }
    }

    #[inline(always)]
    unsafe fn dot_simd(&self, query: &[f32; VEC_DIM], idx: usize) -> f32 {
        let cached = &self.vectors[idx].0;
        let mut acc = _mm256_setzero_ps();
        
        // Process 8 floats per iteration, unrolled 2x for ILP
        for i in (0..VEC_DIM).step_by(16) {
            let q0 = _mm256_load_ps(query.as_ptr().add(i));
            let c0 = _mm256_load_ps(cached.as_ptr().add(i));
            let q1 = _mm256_load_ps(query.as_ptr().add(i + 8));
            let c1 = _mm256_load_ps(cached.as_ptr().add(i + 8));
            
            acc = _mm256_fmadd_ps(q0, c0, acc);
            acc = _mm256_fmadd_ps(q1, c1, acc);
        }
        
        // Horizontal sum
        let acc = _mm256_hadd_ps(acc, acc);
        let acc = _mm256_hadd_ps(acc, acc);
        let lo = _mm256_castps256_ps128(acc);
        let hi = _mm256_extractf128_ps(acc, 1);
        let sum = _mm_add_ps(lo, hi);
        _mm_cvtss_f32(sum)
    }

    #[inline(always)]
    fn query(&mut self, query: &[f32; VEC_DIM]) -> (usize, f32) {
        let mut best_idx = 0;
        let mut best_score = -1e9;
        
        // Branchless scan: ALU-bound, no mispredicts
        for i in 0..CACHE_SIZE {
            let score = unsafe { self.dot_simd(query, i) };
            let is_better = (score > best_score) as usize;
            best_idx = is_better * i + (1 - is_better) * best_idx;
            best_score = f32::max(score, best_score);
        }
        
        self.hits[best_idx] += 1;
        (best_idx, best_score)
    }
}