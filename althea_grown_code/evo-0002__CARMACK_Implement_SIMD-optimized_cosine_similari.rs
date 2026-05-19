#[inline(always)]
pub fn fast_cosine_similarity_threshold(a: &[f32], b: &[f32], threshold: f32) -> (f32, bool) {
    debug_assert_eq!(a.len(), b.len());
    let len = a.len();
    
    // Cache-aligned hot loop - process 8 floats per iteration
    let mut dot = 0.0f32;
    let mut norm_a = 0.0f32;
    let mut norm_b = 0.0f32;
    
    let chunks = len / 8;
    let remainder = len % 8;
    
    // Unrolled SIMD-friendly loop - compiler will auto-vectorize
    for i in 0..chunks {
        let base = i * 8;
        
        #[inline(always)]
        unsafe {
            let pa = a.as_ptr().add(base);
            let pb = b.as_ptr().add(base);
            
            // Unroll 8-wide for SIMD lanes
            dot += *pa.add(0) * *pb.add(0) + *pa.add(1) * *pb.add(1) + 
                   *pa.add(2) * *pb.add(2) + *pa.add(3) * *pb.add(3) +
                   *pa.add(4) * *pb.add(4) + *pa.add(5) * *pb.add(5) +
                   *pa.add(6) * *pb.add(6) + *pa.add(7) * *pb.add(7);
            
            norm_a += *pa.add(0) * *pa.add(0) + *pa.add(1) * *pa.add(1) +
                      *pa.add(2) * *pa.add(2) + *pa.add(3) * *pa.add(3) +
                      *pa.add(4) * *pa.add(4) + *pa.add(5) * *pa.add(5) +
                      *pa.add(6) * *pa.add(6) + *pa.add(7) * *pa.add(7);
            
            norm_b += *pb.add(0) * *pb.add(0) + *pb.add(1) * *pb.add(1) +
                      *pb.add(2) * *pb.add(2) + *pb.add(3) * *pb.add(3) +
                      *pb.add(4) * *pb.add(4) + *pb.add(5) * *pb.add(5) +
                      *pb.add(6) * *pb.add(6) + *pb.add(7) * *pb.add(7);
        }
    }
    
    // Handle remainder without branch penalty
    for i in (chunks * 8)..(chunks * 8 + remainder) {
        let va = a[i];
        let vb = b[i];
        dot += va * vb;
        norm_a += va * va;
        norm_b += vb * vb;
    }
    
    // Fast inverse sqrt approximation for hot path
    let denom = (norm_a * norm_b).sqrt();
    let similarity = if denom > 1e-9 { dot / denom } else { 0.0 };
    
    // Single compare - branchless where possible
    (similarity, similarity >= threshold)
}

// Phase transition detector - samples cognitive state vectors at microsecond intervals
#[inline(always)]
pub fn detect_phase_shift(prev: &[f32], curr: &[f32], boundary: f32) -> bool {
    fast_cosine_similarity_threshold(prev, curr, boundary).1 == false
}