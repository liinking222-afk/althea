use std::arch::x86_64::*;

#[repr(align(64))] // Cache line aligned
pub struct CognitiveWeightMatrix {
    data: Vec<f32>,
    rows: usize,
    cols: usize,
}

impl CognitiveWeightMatrix {
    #[inline(always)]
    pub fn new(rows: usize, cols: usize) -> Self {
        let size = rows * cols;
        let mut data = Vec::with_capacity(size);
        data.resize(size, 0.0f32);
        Self { data, rows, cols }
    }

    #[inline(always)]
    pub fn matmul_simd(&self, rhs: &Self, out: &mut Self) {
        assert!(self.cols == rhs.rows && out.rows == self.rows && out.cols == rhs.cols);
        
        unsafe {
            for i in 0..self.rows {
                for j in (0..rhs.cols).step_by(8) {
                    let mut acc = _mm256_setzero_ps();
                    
                    // Prefetch next cache lines - 2 ahead for temporal locality
                    if i + 2 < self.rows {
                        _mm_prefetch(
                            self.data.as_ptr().add((i + 2) * self.cols) as *const i8,
                            _MM_HINT_T0
                        );
                    }
                    
                    for k in (0..self.cols).step_by(4) {
                        // Load 4 weights from left matrix, broadcast each
                        let a_ptr = self.data.as_ptr().add(i * self.cols + k);
                        
                        for offset in 0..4.min(self.cols - k) {
                            let a_scalar = _mm256_set1_ps(*a_ptr.add(offset));
                            let b_vec = _mm256_loadu_ps(
                                rhs.data.as_ptr().add((k + offset) * rhs.cols + j)
                            );
                            // FMA: acc += a * b (single cycle on modern CPUs)
                            acc = _mm256_fmadd_ps(a_scalar, b_vec, acc);
                        }
                    }
                    
                    _mm256_storeu_ps(out.data.as_mut_ptr().add(i * out.cols + j), acc);
                }
            }
        }
    }
    
    #[inline(always)]
    pub fn get(&self, row: usize, col: usize) -> f32 {
        self.data[row * self.cols + col]
    }
    
    #[inline(always)]
    pub fn set(&mut self, row: usize, col: usize, val: f32) {
        self.data[row * self.cols + col] = val;
    }
}