use std::arch::x86_64::*;

#[repr(C, align(32))]
pub struct VecCache {
    data: [f32; 8],
}

impl VecCache {
    #[inline(always)]
    pub fn new(slice: &[f32]) -> Self {
        let mut data = [0.0f32; 8];
        let len = slice.len().min(8);
        data[..len].copy_from_slice(&slice[..len]);
        VecCache { data }
    }
}

pub struct SemanticDistanceEngine {
    cache: Vec<VecCache>,
    hot_indices: [usize; 16],
    hit_count: usize,
}

impl SemanticDistanceEngine {
    #[inline(always)]
    pub fn new(capacity: usize) -> Self {
        SemanticDistanceEngine {
            cache: Vec::with_capacity(capacity),
            hot_indices: [0; 16],
            hit_count: 0,
        }
    }

    #[inline(always)]
    #[target_feature(enable = "avx2,fma")]
    unsafe fn dot_avx2(a: &[f32; 8], b: &[f32; 8]) -> f32 {
        let va = _mm256_load_ps(a.as_ptr());
        let vb = _mm256_load_ps(b.as_ptr());
        let prod = _mm256_mul_ps(va, vb);
        let sum = _mm256_hadd_ps(prod, prod);
        let sum = _mm256_hadd_ps(sum, sum);
        let lo = _mm256_castps256_ps128(sum);
        let hi = _mm256_extractf128_ps(sum, 1);
        let final_sum = _mm_add_ss(lo, hi);
        _mm_cvtss_f32(final_sum)
    }

    #[inline(always)]
    pub fn distance_hot(&self, idx_a: usize, idx_b: usize) -> f32 {
        unsafe {
            let dot = Self::dot_avx2(&self.cache[idx_a].data, &self.cache[idx_b].data);
            1.0 - dot
        }
    }

    #[inline(always)]
    pub fn push(&mut self, vec: &[f32]) -> usize {
        let idx = self.cache.len();
        self.cache.push(VecCache::new(vec));
        if self.hit_count < 16 {
            self.hot_indices[self.hit_count] = idx;
            self.hit_count += 1;
        }
        idx
    }

    #[inline(always)]
    pub fn scan_hot(&self, query_idx: usize, threshold: f32) -> usize {
        let mut count = 0;
        for &hot_idx in &self.hot_indices[..self.hit_count] {
            if self.distance_hot(query_idx, hot_idx) < threshold {
                count += 1;
            }
        }
        count
    }
}