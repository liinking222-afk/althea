use std::arch::x86_64::*;

#[repr(align(32))]
pub struct VecCache {
    data: Vec<f32>,      // aligned storage for embeddings
    dim: usize,          // embedding dimensionality (must be multiple of 8)
    capacity: usize,     // max vectors
    count: usize,        // current count
    scratch: Vec<f32>,   // aligned scratch buffer for dot products
}

impl VecCache {
    pub fn new(capacity: usize, dim: usize) -> Self {
        assert!(dim % 8 == 0, "dim must be multiple of 8 for AVX");
        let mut data = Vec::with_capacity(capacity * dim);
        data.resize(capacity * dim, 0.0);
        let mut scratch = Vec::with_capacity(dim);
        scratch.resize(dim, 0.0);
        Self { data, dim, capacity, count: 0, scratch }
    }

    #[inline(always)]
    pub fn push(&mut self, vec: &[f32]) -> Option<usize> {
        if self.count >= self.capacity || vec.len() != self.dim { return None; }
        let offset = self.count * self.dim;
        self.data[offset..offset + self.dim].copy_from_slice(vec);
        self.count += 1;
        Some(self.count - 1)
    }

    #[inline(always)]
    pub unsafe fn dot_product_avx(&self, idx: usize, query: &[f32]) -> f32 {
        let offset = idx * self.dim;
        let a = self.data.as_ptr().add(offset);
        let b = query.as_ptr();
        let mut sum = _mm256_setzero_ps();
        
        // Process 8 floats per iteration (256 bits / 32 bits)
        for i in (0..self.dim).step_by(8) {
            let va = _mm256_loadu_ps(a.add(i));
            let vb = _mm256_loadu_ps(b.add(i));
            sum = _mm256_fmadd_ps(va, vb, sum);  // fused multiply-add
        }
        
        // Horizontal sum: reduce 8 lanes to scalar
        let sum128 = _mm_add_ps(_mm256_castps256_ps128(sum), _mm256_extractf128_ps(sum, 1));
        let sum64 = _mm_add_ps(sum128, _mm_movehl_ps(sum128, sum128));
        let sum32 = _mm_add_ss(sum64, _mm_shuffle_ps(sum64, sum64, 1));
        _mm_cvtss_f32(sum32)
    }

    #[inline(always)]
    pub fn top_k(&self, query: &[f32], k: usize) -> Vec<(usize, f32)> {
        let mut scores: Vec<(usize, f32)> = (0..self.count)
            .map(|i| (i, unsafe { self.dot_product_avx(i, query) }))
            .collect();
        
        // Partial sort: only sort first k elements (O(n) average)
        scores.select_nth_unstable_by(k.min(scores.len()) - 1, 
            |a, b| b.1.partial_cmp(&a.1).unwrap());
        scores.truncate(k);
        scores
    }

    #[inline(always)]
    pub fn get(&self, idx: usize) -> Option<&[f32]> {
        if idx >= self.count { return None; }
        let start = idx * self.dim;
        Some(&self.data[start..start + self.dim])
    }
}