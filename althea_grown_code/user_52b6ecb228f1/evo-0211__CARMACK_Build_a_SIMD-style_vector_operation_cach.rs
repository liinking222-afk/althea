use std::arch::x86_64::*;

const CACHE_LINE: usize = 64;
const VEC_WIDTH: usize = 8; // AVX 256-bit = 8x f32

#[repr(align(64))]
pub struct SemanticDistanceCache {
    vectors: Vec<[f32; VEC_WIDTH]>,
    results: Vec<f32>,
    hits: u64,
    misses: u64,
}

impl SemanticDistanceCache {
    #[inline(always)]
    pub fn new(capacity: usize) -> Self {
        let aligned_cap = (capacity + VEC_WIDTH - 1) & !(VEC_WIDTH - 1);
        Self {
            vectors: Vec::with_capacity(aligned_cap / VEC_WIDTH),
            results: Vec::with_capacity(aligned_cap),
            hits: 0,
            misses: 0,
        }
    }

    #[inline(always)]
    pub fn cosine_simd(&mut self, a: &[f32], b: &[f32]) -> f32 {
        debug_assert_eq!(a.len(), b.len());
        debug_assert_eq!(a.len() % VEC_WIDTH, 0);
        
        unsafe {
            let mut dot = _mm256_setzero_ps();
            let mut norm_a = _mm256_setzero_ps();
            let mut norm_b = _mm256_setzero_ps();
            
            // Hot loop: unrolled SIMD over cache-aligned chunks
            for i in (0..a.len()).step_by(VEC_WIDTH) {
                let va = _mm256_loadu_ps(a.as_ptr().add(i));
                let vb = _mm256_loadu_ps(b.as_ptr().add(i));
                
                dot = _mm256_fmadd_ps(va, vb, dot); // FMA: dot += a*b
                norm_a = _mm256_fmadd_ps(va, va, norm_a);
                norm_b = _mm256_fmadd_ps(vb, vb, norm_b);
            }
            
            // Horizontal reduction with minimal shuffle
            let dot_val = Self::hsum_avx(dot);
            let norm_a_val = Self::hsum_avx(norm_a).sqrt();
            let norm_b_val = Self::hsum_avx(norm_b).sqrt();
            
            dot_val / (norm_a_val * norm_b_val + 1e-8)
        }
    }
    
    #[inline(always)]
    unsafe fn hsum_avx(v: __m256) -> f32 {
        let hi = _mm256_extractf128_ps(v, 1);
        let lo = _mm256_castps256_ps128(v);
        let sum128 = _mm_add_ps(hi, lo);
        let shuf = _mm_movehdup_ps(sum128);
        let sums = _mm_add_ps(sum128, shuf);
        let shuf2 = _mm_movehl_ps(shuf, sums);
        let result = _mm_add_ss(sums, shuf2);
        _mm_cvtss_f32(result)
    }
    
    #[inline(always)]
    pub fn metrics(&self) -> (u64, u64, f32) {
        let total = self.hits + self.misses;
        let hit_rate = if total > 0 { self.hits as f32 / total as f32 } else { 0.0 };
        (self.hits, self.misses, hit_rate)
    }
}