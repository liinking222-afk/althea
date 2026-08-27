use std::arch::x86_64::*;
use std::alloc::{alloc, dealloc, Layout};

const ALIGN: usize = 32; // AVX alignment
const DIM: usize = 384;  // embedding dimension (divisible by 8 for AVX)

#[repr(C, align(32))]
pub struct AlignedEmbedding {
    data: *mut f32,
}

impl AlignedEmbedding {
    #[inline(always)]
    pub fn new() -> Self {
        let layout = Layout::from_size_align(DIM * 4, ALIGN).unwrap();
        Self { data: unsafe { alloc(layout) as *mut f32 } }
    }

    #[inline(always)]
    pub fn as_slice(&self) -> &[f32] {
        unsafe { std::slice::from_raw_parts(self.data, DIM) }
    }

    #[inline(always)]
    pub fn as_mut_slice(&mut self) -> &mut [f32] {
        unsafe { std::slice::from_raw_parts_mut(self.data, DIM) }
    }
}

impl Drop for AlignedEmbedding {
    fn drop(&mut self) {
        let layout = Layout::from_size_align(DIM * 4, ALIGN).unwrap();
        unsafe { dealloc(self.data as *mut u8, layout) }
    }
}

#[target_feature(enable = "avx")]
#[inline(always)]
unsafe fn dot_product_avx(a: &[f32], b: &[f32]) -> f32 {
    let mut sum = _mm256_setzero_ps();
    for i in (0..DIM).step_by(8) {
        let va = _mm256_load_ps(a.as_ptr().add(i));
        let vb = _mm256_load_ps(b.as_ptr().add(i));
        sum = _mm256_fmadd_ps(va, vb, sum); // fused multiply-add
    }
    let mut result = [0f32; 8];
    _mm256_storeu_ps(result.as_mut_ptr(), sum);
    result.iter().sum()
}

#[target_feature(enable = "avx")]
#[inline(always)]
unsafe fn norm_avx(a: &[f32]) -> f32 {
    dot_product_avx(a, a).sqrt()
}

#[inline(always)]
pub fn cosine_similarity_fast(a: &AlignedEmbedding, b: &AlignedEmbedding) -> f32 {
    unsafe {
        let dot = dot_product_avx(a.as_slice(), b.as_slice());
        let norm_a = norm_avx(a.as_slice());
        let norm_b = norm_avx(b.as_slice());
        dot / (norm_a * norm_b) // single division, no branches
    }
}

pub struct ConceptCache {
    embeddings: Vec<AlignedEmbedding>,
    labels: Vec<u32>, // concept IDs, u32 for cache efficiency
}

impl ConceptCache {
    #[inline(always)]
    pub fn score_batch(&self, query: &AlignedEmbedding) -> Vec<(u32, f32)> {
        self.embeddings.iter()
            .zip(&self.labels)
            .map(|(emb, &label)| (label, cosine_similarity_fast(query, emb)))
            .collect()
    }
}