use std::arch::x86_64::*;

#[repr(align(32))]
pub struct AlignedVec {
    data: Vec<f32>,
    len: usize,
}

impl AlignedVec {
    #[inline(always)]
    pub fn new(size: usize) -> Self {
        let mut v = Vec::with_capacity(size + 8);
        v.resize(size, 0.0f32);
        AlignedVec { data: v, len: size }
    }

    #[inline(always)]
    pub fn dot_simd(&self, other: &AlignedVec) -> f32 {
        debug_assert_eq!(self.len, other.len);
        unsafe { self.dot_simd_unchecked(other) }
    }

    #[target_feature(enable = "avx2,fma")]
    unsafe fn dot_simd_unchecked(&self, other: &AlignedVec) -> f32 {
        let mut acc = _mm256_setzero_ps();
        let chunks = self.len / 8;
        let ptr_a = self.data.as_ptr();
        let ptr_b = other.data.as_ptr();

        // Unroll 4x for better ILP
        let mut i = 0;
        while i + 32 <= self.len {
            let a0 = _mm256_load_ps(ptr_a.add(i));
            let b0 = _mm256_load_ps(ptr_b.add(i));
            let a1 = _mm256_load_ps(ptr_a.add(i + 8));
            let b1 = _mm256_load_ps(ptr_b.add(i + 8));
            let a2 = _mm256_load_ps(ptr_a.add(i + 16));
            let b2 = _mm256_load_ps(ptr_b.add(i + 16));
            let a3 = _mm256_load_ps(ptr_a.add(i + 24));
            let b3 = _mm256_load_ps(ptr_b.add(i + 24));

            acc = _mm256_fmadd_ps(a0, b0, acc);
            acc = _mm256_fmadd_ps(a1, b1, acc);
            acc = _mm256_fmadd_ps(a2, b2, acc);
            acc = _mm256_fmadd_ps(a3, b3, acc);
            i += 32;
        }

        // Tail: process remaining 8-wide chunks
        while i + 8 <= self.len {
            let a = _mm256_load_ps(ptr_a.add(i));
            let b = _mm256_load_ps(ptr_b.add(i));
            acc = _mm256_fmadd_ps(a, b, acc);
            i += 8;
        }

        // Horizontal sum: cache the shuffle pattern
        let low = _mm256_castps256_ps128(acc);
        let high = _mm256_extractf128_ps(acc, 1);
        let sum128 = _mm_add_ps(low, high);
        let shuf = _mm_movehdup_ps(sum128);
        let sums = _mm_add_ps(sum128, shuf);
        let shuf2 = _mm_movehl_ps(shuf, sums);
        let result = _mm_add_ss(sums, shuf2);

        _mm_cvtss_f32(result)
    }
}