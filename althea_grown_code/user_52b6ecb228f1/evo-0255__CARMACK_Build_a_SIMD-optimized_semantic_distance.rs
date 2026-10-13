#![allow(dead_code)]
use std::arch::x86_64::*;

const CACHE_SIZE: usize = 512; // Power of 2 for mask ops
const VEC_DIM: usize = 64; // SIMD-friendly dimension
const BUCKET_MASK: usize = CACHE_SIZE - 1;

#[repr(align(64))] // Cache line alignment
struct SemanticCache {
    vectors: [[f32; VEC_DIM]; CACHE_SIZE],
    ids: [u64; CACHE_SIZE],
    scores: [f32; CACHE_SIZE],
    writes: usize,
}

impl SemanticCache {
    #[inline(always)]
    fn new() -> Self {
        Self {
            vectors: [[0.0; VEC_DIM]; CACHE_SIZE],
            ids: [0; CACHE_SIZE],
            scores: [0.0; CACHE_SIZE],
            writes: 0,
        }
    }

    #[inline(always)]
    fn hash(&self, id: u64) -> usize {
        ((id.wrapping_mul(0x517cc1b727220a95)) >> 55) as usize & BUCKET_MASK
    }

    #[inline(always)]
    unsafe fn dot_simd(&self, a: &[f32; VEC_DIM], b: &[f32; VEC_DIM]) -> f32 {
        let mut acc = _mm256_setzero_ps();
        for i in (0..VEC_DIM).step_by(8) {
            let va = _mm256_loadu_ps(a.as_ptr().add(i));
            let vb = _mm256_loadu_ps(b.as_ptr().add(i));
            acc = _mm256_fmadd_ps(va, vb, acc); // Fused multiply-add
        }
        let mut tmp = [0.0f32; 8];
        _mm256_storeu_ps(tmp.as_mut_ptr(), acc);
        tmp.iter().sum() // Horizontal sum in registers
    }

    #[inline(always)]
    fn insert(&mut self, id: u64, vec: [f32; VEC_DIM]) {
        let idx = self.hash(id);
        self.vectors[idx] = vec;
        self.ids[idx] = id;
        self.writes += 1;
    }

    #[inline(always)]
    fn query(&self, vec: &[f32; VEC_DIM], top_k: usize) -> Vec<(u64, f32)> {
        let mut results: Vec<(usize, f32)> = (0..CACHE_SIZE)
            .map(|i| unsafe { (i, self.dot_simd(vec, &self.vectors[i])) })
            .collect();
        
        results.select_nth_unstable_by(top_k, |a, b| b.1.partial_cmp(&a.1).unwrap());
        results[..top_k]
            .iter()
            .map(|&(i, score)| (self.ids[i], score))
            .collect()
    }
}

pub fn create_cache() -> SemanticCache {
    SemanticCache::new()
}