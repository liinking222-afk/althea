#[repr(align(64))]
pub struct CoherenceMetrics {
    samples: [i32; 256],      // fixed-point Q16.16, cache-line aligned
    weights: [i32; 256],      // precomputed weight LUT
    head: u8,
    count: u8,
}

impl CoherenceMetrics {
    #[inline(always)]
    pub const fn new() -> Self {
        Self { samples: [0; 256], weights: Self::gen_weights(), head: 0, count: 0 }
    }

    // Precompute at compile-time: exponential decay weights in fixed-point
    const fn gen_weights() -> [i32; 256] {
        let mut w = [0i32; 256];
        let mut i = 0;
        while i < 256 {
            // w[i] = exp(-i/64.0) in Q16.16, approximated: 65536 * (255-i) / 255
            w[i] = (65536 * (255 - i as i32)) / 255;
            i += 1;
        }
        w
    }

    #[inline(always)]
    pub fn push(&mut self, value: f32) {
        // Convert float to Q16.16 fixed-point inline
        self.samples[self.head as usize] = (value * 65536.0) as i32;
        self.head = self.head.wrapping_add(1);
        if self.count < 255 { self.count += 1; }
    }

    #[inline(always)]
    pub fn coherence(&self) -> f32 {
        let n = self.count as usize;
        if n < 4 { return 0.0; }
        
        let mut sum: i64 = 0;
        let mut sq_sum: i64 = 0;
        
        // Unrolled hot loop: process 4 samples per iteration
        let base = self.head.wrapping_sub(self.count);
        let chunks = n >> 2;
        for c in 0..chunks {
            let i0 = base.wrapping_add((c << 2) as u8) as usize;
            let i1 = base.wrapping_add((c << 2 | 1) as u8) as usize;
            let i2 = base.wrapping_add((c << 2 | 2) as u8) as usize;
            let i3 = base.wrapping_add((c << 2 | 3) as u8) as usize;
            
            let s0 = self.samples[i0] as i64 * self.weights[c << 2] as i64;
            let s1 = self.samples[i1] as i64 * self.weights[c << 2 | 1] as i64;
            let s2 = self.samples[i2] as i64 * self.weights[c << 2 | 2] as i64;
            let s3 = self.samples[i3] as i64 * self.weights[c << 2 | 3] as i64;
            
            sum += s0 + s1 + s2 + s3;
            sq_sum += (s0 * s0 + s1 * s1 + s2 * s2 + s3 * s3) >> 16;
        }
        
        // Variance in Q16.16: E[X²] - E[X]²
        let mean = sum / n as i64;
        let variance = (sq_sum / n as i64) - ((mean * mean) >> 16);
        
        // Coherence = 1 / (1 + normalized_stddev), return as float
        let stddev = (variance.max(0) as f32).sqrt();
        65536.0 / (65536.0 + stddev)
    }
}