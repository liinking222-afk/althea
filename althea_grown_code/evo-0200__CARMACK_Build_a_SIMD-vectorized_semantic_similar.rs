use std::arch::x86_64::*;
use std::alloc::{alloc, dealloc, Layout};

const VEC_DIM: usize = 64; // Cache-line aligned dimension
const ALIGN: usize = 64;

#[repr(align(64))]
struct AlignedVec {
    ptr: *mut f32,
    len: usize,
}

impl AlignedVec {
    #[inline(always)]
    fn new(size: usize) -> Self {
        let layout = Layout::from_size_align(size * 4, ALIGN).unwrap();
        let ptr = unsafe { alloc(layout) as *mut f32 };
        AlignedVec { ptr, len: size }
    }
    
    #[inline(always)]
    unsafe fn get_slice(&self) -> &[f32] {
        std::slice::from_raw_parts(self.ptr, self.len)
    }
}

impl Drop for AlignedVec {
    fn drop(&mut self) {
        unsafe {
            dealloc(self.ptr as *mut u8, Layout::from_size_align(self.len * 4, ALIGN).unwrap());
        }
    }
}

#[target_feature(enable = "avx2,fma")]
#[inline(always)]
unsafe fn dot_product_simd(a: *const f32, b: *const f32, n: usize) -> f32 {
    let mut sum = _mm256_setzero_ps();
    let chunks = n / 8;
    
    for i in 0..chunks {
        let offset = i * 8;
        let va = _mm256_load_ps(a.add(offset)); // Aligned load = 1 cycle
        let vb = _mm256_load_ps(b.add(offset));
        sum = _mm256_fmadd_ps(va, vb, sum); // FMA = 4 cycles latency, 0.5 throughput
    }
    
    // Horizontal sum: 8 floats -> 1
    let sum128 = _mm_add_ps(_mm256_castps256_ps128(sum), _mm256_extractf128_ps(sum, 1));
    let sum64 = _mm_add_ps(sum128, _mm_movehl_ps(sum128, sum128));
    let sum32 = _mm_add_ss(sum64, _mm_shuffle_ps(sum64, sum64, 0x55));
    _mm_cvtss_f32(sum32)
}

pub struct SemanticScorer {
    embeddings: Vec<AlignedVec>,
    norms: Vec<f32>, // Precomputed for division reuse
}

impl SemanticScorer {
    pub fn new(capacity: usize) -> Self {
        SemanticScorer { embeddings: Vec::with_capacity(capacity), norms: Vec::with_capacity(capacity) }
    }
    
    #[inline(always)]
    pub fn add_concept(&mut self, vec: &[f32]) {
        let mut aligned = AlignedVec::new(VEC_DIM);
        unsafe {
            std::ptr::copy_nonoverlapping(vec.as_ptr(), aligned.ptr, VEC_DIM.min(vec.len()));
            let norm = dot_product_simd(aligned.ptr, aligned.ptr, VEC_DIM).sqrt();
            self.norms.push(1.0 / norm); // Reciprocal for multiply-not-divide
            self.embeddings.push(aligned);
        }
    }
    
    #[inline(always)]
    pub fn cosine_similarity(&self, idx_a: usize, idx_b: usize) -> f32 {
        unsafe {
            let dot = dot_product_simd(self.embeddings[idx_a].ptr, self.embeddings[idx_b].ptr, VEC_DIM);
            dot * self.norms[idx_a] * self.norms[idx_b] // 2 muls faster than 1 div
        }
    }
}