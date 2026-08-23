#[inline(always)]
fn fast_cosine_similarity(a: &[i16; 64], b: &[i16; 64]) -> i32 {
    let mut dot: i32 = 0;
    let mut norm_a: i32 = 0;
    let mut norm_b: i32 = 0;
    
    // Unroll by 4 for instruction-level parallelism
    let mut i = 0;
    while i < 64 {
        let a0 = a[i] as i32; let b0 = b[i] as i32;
        let a1 = a[i+1] as i32; let b1 = b[i+1] as i32;
        let a2 = a[i+2] as i32; let b2 = b[i+2] as i32;
        let a3 = a[i+3] as i32; let b3 = b[i+3] as i32;
        
        dot += a0*b0 + a1*b1 + a2*b2 + a3*b3;
        norm_a += a0*a0 + a1*a1 + a2*a2 + a3*a3;
        norm_b += b0*b0 + b1*b1 + b2*b2 + b3*b3;
        i += 4;
    }
    
    // Fixed-point: scale by 1024, avoid sqrt via approximation
    let inv_sqrt_a = fast_inv_sqrt(norm_a);
    let inv_sqrt_b = fast_inv_sqrt(norm_b);
    (dot * inv_sqrt_a * inv_sqrt_b) >> 20 // Result in range [-1024, 1024]
}

#[inline(always)]
fn fast_inv_sqrt(x: i32) -> i32 {
    // Integer approximation of 1/sqrt(x) scaled by 1024
    if x <= 0 { return 0; }
    let mut r = (1024 << 10) / ((x >> 10).max(1));
    r = (r + (1024 << 10) / r) >> 1; // Newton iteration
    r
}

pub struct CoherenceCache {
    baseline: [i16; 64],    // Core identity vector (quantized)
    recent: [[i16; 64]; 8], // Ring buffer of recent outputs
    idx: usize,
    drift_threshold: i32,   // Scaled by 1024: 819 = 0.8 similarity
}

impl CoherenceCache {
    #[inline(always)]
    pub fn check_drift(&self) -> bool {
        let sim = fast_cosine_similarity(&self.baseline, &self.recent[self.idx]);
        sim < self.drift_threshold // True = drift detected
    }
    
    #[inline(always)]
    pub fn update(&mut self, vec: &[i16; 64]) {
        self.idx = (self.idx + 1) & 7; // Branchless modulo-8
        self.recent[self.idx] = *vec;
    }
}