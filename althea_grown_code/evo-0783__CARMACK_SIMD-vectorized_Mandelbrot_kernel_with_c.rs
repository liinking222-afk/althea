#![no_std]
use core::arch::x86_64::*;

#[repr(C, align(32))]
pub struct MandelKernel {
    max_iter: u32,
    bailout_sq: f32,
}

impl MandelKernel {
    #[inline(always)]
    pub const fn new(max_iter: u32) -> Self {
        Self { max_iter, bailout_sq: 4.0 }
    }

    #[inline(always)]
    #[target_feature(enable = "avx2,fma")]
    pub unsafe fn compute_scanline_avx2(
        &self,
        y: f32,
        x_start: f32,
        dx: f32,
        width: usize,
        out: &mut [u32],
    ) {
        let max = _mm256_set1_ps(self.bailout_sq);
        let iter_max = _mm256_set1_epi32(self.max_iter as i32);
        let cy = _mm256_set1_ps(y);
        
        // Process 8 pixels per iteration - cache line aligned
        for i in (0..width).step_by(8) {
            let offset = _mm256_set_ps(7.0, 6.0, 5.0, 4.0, 3.0, 2.0, 1.0, 0.0);
            let cx = _mm256_fmadd_ps(
                _mm256_set1_ps(dx),
                _mm256_add_ps(_mm256_set1_ps(i as f32), offset),
                _mm256_set1_ps(x_start),
            );

            let mut zr = _mm256_setzero_ps();
            let mut zi = _mm256_setzero_ps();
            let mut iters = _mm256_setzero_si256();
            
            // Hot loop - minimize branches, maximize FMA units
            for _ in 0..self.max_iter {
                let zr2 = _mm256_mul_ps(zr, zr);
                let zi2 = _mm256_mul_ps(zi, zi);
                let mag = _mm256_add_ps(zr2, zi2);
                
                let mask = _mm256_cmp_ps(mag, max, _CMP_LT_OQ);
                if _mm256_movemask_ps(mask) == 0 { break; } // Early exit
                
                let new_zi = _mm256_fmadd_ps(_mm256_set1_ps(2.0), _mm256_mul_ps(zr, zi), cy);
                zr = _mm256_add_ps(_mm256_sub_ps(zr2, zi2), cx);
                zi = new_zi;
                
                iters = _mm256_sub_epi32(iters, _mm256_castps_si256(mask));
            }
            
            _mm256_storeu_si256(out.as_mut_ptr().add(i) as *mut __m256i, iters);
        }
    }
}