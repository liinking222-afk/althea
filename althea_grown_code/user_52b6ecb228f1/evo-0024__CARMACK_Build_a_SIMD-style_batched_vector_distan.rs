use std::arch::x86_64::*;

#[repr(align(32))]
pub struct AlignedVec {
    pub data: Vec<f32>,
}

// Batched L2 distance: processes 4 pairs simultaneously, cache-hot, branch-free
// WHY: Scaffold interpolation needs O(n²) distance matrix; cut cycles by 4x minimum
#[inline(always)]
pub unsafe fn batch_l2_distance_x4(
    a: &[f32; 32], // 4 vectors of dim 8, packed tight
    b: &[f32; 32],
) -> [f32; 4] {
    let mut sums = _mm256_setzero_ps();
    
    // Unroll 4 iterations: 8 dims per vector, stride pattern eliminates cache miss
    for i in 0..4 {
        let offset = i * 8;
        let va = _mm256_loadu_ps(a.as_ptr().add(offset));
        let vb = _mm256_loadu_ps(b.as_ptr().add(offset));
        let diff = _mm256_sub_ps(va, vb);
        sums = _mm256_fmadd_ps(diff, diff, sums); // Fused multiply-add: 1 cycle not 2
    }
    
    // Horizontal reduction: sum 8 lanes into 4 distances
    let mut result = [0.0f32; 4];
    let temp: [f32; 8] = std::mem::transmute(sums);
    
    // Manual reduction: compiler vectorizes this loop
    for i in 0..4 {
        result[i] = temp[i * 2] + temp[i * 2 + 1];
        result[i] = result[i].sqrt(); // Single sqrt per result, not per component
    }
    
    result
}

// Precompute distance matrix for N capability vectors in batches of 4
// Memory layout: row-major, prefetch-friendly
pub unsafe fn compute_distance_matrix(vectors: &[[f32; 8]], output: &mut [f32]) {
    let n = vectors.len();
    let mut batch_a = [0.0f32; 32];
    let mut batch_b = [0.0f32; 32];
    
    for i in (0..n).step_by(4) {
        for j in (0..n).step_by(4) {
            // Pack 4 vectors into aligned batch
            for k in 0..4.min(n - i) {
                batch_a[k * 8..(k + 1) * 8].copy_from_slice(&vectors[i + k]);
            }
            for k in 0..4.min(n - j) {
                batch_b[k * 8..(k + 1) * 8].copy_from_slice(&vectors[j + k]);
            }
            
            let distances = batch_l2_distance_x4(&batch_a, &batch_b);
            
            // Write results to output matrix
            for k in 0..4.min(n - i) {
                for l in 0..4.min(n - j) {
                    output[(i + k) * n + (j + l)] = distances[k.min(l)];
                }
            }
        }
    }
}