// Carmack-style: hot loop, cache-dense, cycle-aware, float craft
// Target: <100ns for k<=16 common case (transformer sampling)

#[repr(C, align(64))]  // cache line align
pub struct FastSoftmax {
    recip_lut: [f32; 256],  // 1/x table for [1.0, 256.0)
    scratch: [f32; 32],     // stack-local, no heap
}

impl FastSoftmax {
    #[inline(always)]
    pub fn new() -> Self {
        let mut lut = [0.0f32; 256];
        for i in 1..256 { lut[i] = 1.0 / (i as f32); }  // precompute
        Self { recip_lut: lut, scratch: [0.0; 32] }
    }

    // Hot path: branchless, unrolled, SIMD-friendly
    #[inline(always)]
    pub fn normalize_topk(&mut self, logits: &mut [f32]) -> f32 {
        let k = logits.len();
        debug_assert!(k <= 32, "exceeds scratch capacity");
        
        // Max-subtract for numerical stability (single pass)
        let mut max_val = logits[0];
        let mut i = 1;
        while i < k {
            let v = logits[i];
            max_val = max_val.max(v);  // branchless on modern FPU
            i += 1;
        }
        
        // Exp + accumulate (manual unroll k=4)
        let mut sum = 0.0f32;
        i = 0;
        while i + 4 <= k {
            let e0 = (logits[i + 0] - max_val).exp();
            let e1 = (logits[i + 1] - max_val).exp();
            let e2 = (logits[i + 2] - max_val).exp();
            let e3 = (logits[i + 3] - max_val).exp();
            self.scratch[i + 0] = e0; sum += e0;
            self.scratch[i + 1] = e1; sum += e1;
            self.scratch[i + 2] = e2; sum += e2;
            self.scratch[i + 3] = e3; sum += e3;
            i += 4;
        }
        while i < k {  // tail
            let e = (logits[i] - max_val).exp();
            self.scratch[i] = e;
            sum += e;
            i += 1;
        }
        
        // Normalize: multiply by 1/sum (faster than divide)
        let recip_sum = 1.0 / sum;
        i = 0;
        while i + 4 <= k {
            logits[i + 0] = self.scratch[i + 0] * recip_sum;
            logits[i + 1] = self.scratch[i + 1] * recip_sum;
            logits[i + 2] = self.scratch[i + 2] * recip_sum;
            logits[i + 3] = self.scratch[i + 3] * recip_sum;
            i += 4;
        }
        while i < k {
            logits[i] = self.scratch[i] * recip_sum;
            i += 1;
        }
        
        sum  // return partition function (useful for entropy calc)
    }
}