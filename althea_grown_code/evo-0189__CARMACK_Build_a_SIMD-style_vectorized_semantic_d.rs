use std::arch::x86_64::*;
use std::alloc::{alloc, dealloc, Layout};

const VECTOR_DIM: usize = 64;
const CACHE_LINE: usize = 64;

#[repr(align(64))]
struct AlignedVector {
    data: *mut f32,
    len: usize,
}

impl AlignedVector {
    #[inline(always)]
    fn new(dim: usize) -> Self {
        let layout = Layout::from_size_align(dim * 4, CACHE_LINE).unwrap();
        let data = unsafe { alloc(layout) as *mut f32 };
        AlignedVector { data, len: dim }
    }

    #[inline(always)]
    unsafe fn cosine_similarity_avx(&self, other: &AlignedVector) -> f32 {
        let mut dot = _mm256_setzero_ps();
        let mut norm_a = _mm256_setzero_ps();
        let mut norm_b = _mm256_setzero_ps();
        
        // 8 floats per AVX register, unroll 2x for ILP
        let chunks = self.len / 16;
        for i in 0..chunks {
            let offset = i * 16;
            
            let a0 = _mm256_load_ps(self.data.add(offset));
            let b0 = _mm256_load_ps(other.data.add(offset));
            let a1 = _mm256_load_ps(self.data.add(offset + 8));
            let b1 = _mm256_load_ps(other.data.add(offset + 8));
            
            dot = _mm256_fmadd_ps(a0, b0, dot);
            norm_a = _mm256_fmadd_ps(a0, a0, norm_a);
            norm_b = _mm256_fmadd_ps(b0, b0, norm_b);
            
            dot = _mm256_fmadd_ps(a1, b1, dot);
            norm_a = _mm256_fmadd_ps(a1, a1, norm_a);
            norm_b = _mm256_fmadd_ps(b1, b1, norm_b);
        }
        
        // Horizontal reduction (minimize register->memory traffic)
        let dot_sum = hsum_avx(dot);
        let norm_a_sum = hsum_avx(norm_a);
        let norm_b_sum = hsum_avx(norm_b);
        
        dot_sum * (norm_a_sum * norm_b_sum).sqrt().recip()
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

impl Drop for AlignedVector {
    fn drop(&mut self) {
        unsafe {
            let layout = Layout::from_size_align_unchecked(self.len * 4, CACHE_LINE);
            dealloc(self.data as *mut u8, layout);
        }
    }
}