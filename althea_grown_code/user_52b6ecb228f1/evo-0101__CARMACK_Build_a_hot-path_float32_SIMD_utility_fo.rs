#![allow(dead_code)]
use std::arch::x86_64::*;

#[repr(C, align(32))]
pub struct Vec3Batch {
    x: [f32; 8],
    y: [f32; 8],
    z: [f32; 8],
}

impl Vec3Batch {
    #[inline(always)]
    pub fn new() -> Self {
        Self { x: [0.0; 8], y: [0.0; 8], z: [0.0; 8] }
    }

    #[inline(always)]
    pub unsafe fn dot_batch(&self, other: &Vec3Batch, out: &mut [f32; 8]) {
        let x1 = _mm256_load_ps(self.x.as_ptr());
        let y1 = _mm256_load_ps(self.y.as_ptr());
        let z1 = _mm256_load_ps(self.z.as_ptr());
        let x2 = _mm256_load_ps(other.x.as_ptr());
        let y2 = _mm256_load_ps(other.y.as_ptr());
        let z2 = _mm256_load_ps(other.z.as_ptr());
        
        let mx = _mm256_mul_ps(x1, x2);
        let my = _mm256_mul_ps(y1, y2);
        let mz = _mm256_mul_ps(z1, z2);
        let sum = _mm256_add_ps(_mm256_add_ps(mx, my), mz);
        
        _mm256_store_ps(out.as_mut_ptr(), sum);
    }

    #[inline(always)]
    pub unsafe fn length_sq_batch(&self, out: &mut [f32; 8]) {
        self.dot_batch(self, out);
    }

    #[inline(always)]
    pub unsafe fn normalize_batch(&mut self) {
        let mut len_sq = [0.0f32; 8];
        self.length_sq_batch(&mut len_sq);
        
        let lengths = _mm256_load_ps(len_sq.as_ptr());
        let rsqrt = _mm256_rsqrt_ps(lengths); // Fast inverse sqrt
        
        let x = _mm256_load_ps(self.x.as_ptr());
        let y = _mm256_load_ps(self.y.as_ptr());
        let z = _mm256_load_ps(self.z.as_ptr());
        
        _mm256_store_ps(self.x.as_mut_ptr(), _mm256_mul_ps(x, rsqrt));
        _mm256_store_ps(self.y.as_mut_ptr(), _mm256_mul_ps(y, rsqrt));
        _mm256_store_ps(self.z.as_mut_ptr(), _mm256_mul_ps(z, rsqrt));
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    
    #[test]
    fn test_dot() {
        let mut a = Vec3Batch::new();
        a.x = [1.0; 8];
        let mut out = [0.0; 8];
        unsafe { a.dot_batch(&a, &mut out); }
        assert_eq!(out[0], 1.0);
    }
}