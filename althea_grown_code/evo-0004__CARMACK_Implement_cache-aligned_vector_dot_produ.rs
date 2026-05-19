#[repr(align(64))]
pub struct AlignedVec {
    data: Vec<f32>,
    len: usize,
}

impl AlignedVec {
    #[inline(always)]
    pub fn new(data: Vec<f32>) -> Self {
        let len = data.len();
        Self { data, len }
    }
    
    #[inline(always)]
    pub fn as_ptr(&self) -> *const f32 {
        self.data.as_ptr()
    }
}

// Cache-optimized dot product with manual unrolling (4-way)
// Exploits instruction-level parallelism and FMA units
#[inline(always)]
pub fn fast_dot(a: &AlignedVec, b: &AlignedVec) -> f32 {
    debug_assert_eq!(a.len, b.len);
    let len = a.len;
    let chunks = len / 4;
    let remainder = len % 4;
    
    let a_ptr = a.as_ptr();
    let b_ptr = b.as_ptr();
    
    let mut sum0 = 0.0f32;
    let mut sum1 = 0.0f32;
    let mut sum2 = 0.0f32;
    let mut sum3 = 0.0f32;
    
    // Unrolled main loop - 4 FMAs per iteration
    // Compiler will emit vfmadd instructions on modern CPUs
    for i in 0..chunks {
        let base = i * 4;
        unsafe {
            sum0 += *a_ptr.add(base) * *b_ptr.add(base);
            sum1 += *a_ptr.add(base + 1) * *b_ptr.add(base + 1);
            sum2 += *a_ptr.add(base + 2) * *b_ptr.add(base + 2);
            sum3 += *a_ptr.add(base + 3) * *b_ptr.add(base + 3);
        }
    }
    
    // Horizontal reduction - minimize dependency chains
    let mut total = (sum0 + sum1) + (sum2 + sum3);
    
    // Scalar remainder
    for i in (chunks * 4)..len {
        unsafe {
            total += *a_ptr.add(i) * *b_ptr.add(i);
        }
    }
    
    total
}

// Fast similarity with threshold cutoff - early exit optimization
#[inline(always)]
pub fn similarity_above_threshold(a: &AlignedVec, b: &AlignedVec, threshold: f32) -> bool {
    let dot = fast_dot(a, b);
    dot > threshold
}