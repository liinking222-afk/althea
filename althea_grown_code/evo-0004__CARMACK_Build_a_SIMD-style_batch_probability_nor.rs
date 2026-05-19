#![allow(dead_code)]
use std::arch::x86_64::*;

const RECIP_TABLE_BITS: usize = 12;
const RECIP_TABLE_SIZE: usize = 1 << RECIP_TABLE_BITS;
static mut RECIP_TABLE: [f32; RECIP_TABLE_SIZE] = [0.0; RECIP_TABLE_SIZE];

#[inline(always)]
unsafe fn init_recip_table() {
    for i in 1..RECIP_TABLE_SIZE {
        RECIP_TABLE[i] = 1.0 / (i as f32);
    }
    RECIP_TABLE[0] = 0.0;
}

#[inline(always)]
fn fast_recip(x: f32) -> f32 {
    unsafe {
        let idx = (x * (RECIP_TABLE_SIZE as f32 - 1.0)) as usize;
        let clamped = idx.min(RECIP_TABLE_SIZE - 1);
        *RECIP_TABLE.get_unchecked(clamped)
    }
}

#[inline(always)]
pub unsafe fn batch_normalize_simd(logits: &mut [f32]) {
    let len = logits.len();
    let chunks = len / 8;
    
    // Phase 1: Vectorized exp approximation via bit hacks
    let mut sum_vec = _mm256_setzero_ps();
    for i in 0..chunks {
        let offset = i * 8;
        let v = _mm256_loadu_ps(logits.as_ptr().add(offset));
        let exp_approx = _mm256_mul_ps(v, _mm256_set1_ps(1.4426950408889634)); // log2(e)
        let shifted = _mm256_add_ps(exp_approx, _mm256_set1_ps(127.0));
        let casted = _mm256_castps_si256(shifted);
        let shifted_int = _mm256_slli_epi32(casted, 23);
        let result = _mm256_castsi256_ps(shifted_int);
        _mm256_storeu_ps(logits.as_mut_ptr().add(offset), result);
        sum_vec = _mm256_add_ps(sum_vec, result);
    }
    
    // Horizontal sum extraction (branchless)
    let mut sum_array = [0.0f32; 8];
    _mm256_storeu_ps(sum_array.as_mut_ptr(), sum_vec);
    let mut total = sum_array[0] + sum_array[1] + sum_array[2] + sum_array[3]
                  + sum_array[4] + sum_array[5] + sum_array[6] + sum_array[7];
    
    // Tail elements (cache-friendly sequential)
    for i in (chunks * 8)..len {
        total += logits[i];
    }
    
    // Phase 2: Multiply by reciprocal (single division becomes broadcast)
    let recip = 1.0 / total;
    let recip_vec = _mm256_set1_ps(recip);
    for i in 0..chunks {
        let offset = i * 8;
        let v = _mm256_loadu_ps(logits.as_ptr().add(offset));
        let normalized = _mm256_mul_ps(v, recip_vec);
        _mm256_storeu_ps(logits.as_mut_ptr().add(offset), normalized);
    }
    for i in (chunks * 8)..len {
        logits[i] *= recip;
    }
}

pub fn init() { unsafe { init_recip_table(); } }