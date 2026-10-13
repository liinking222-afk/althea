#[inline(always)]
const fn fp_from_float(x: f32) -> i64 {
    (x * 65536.0) as i64
}

#[inline(always)]
const fn fp_mul(a: i64, b: i64) -> i64 {
    (a * b) >> 16
}

#[inline(always)]
const fn fp_add(a: i64, b: i64) -> i64 {
    a + b
}

#[inline(always)]
const fn fp_to_float(x: i64) -> f32 {
    (x as f32) / 65536.0
}

#[inline(always)]
fn fp_exp_approx(x: i64) -> i64 {
    // Pade approximation for exp(x) in fixed-point, x in [-1, 1]
    let x_clamped = x.max(-65536).min(65536);
    let x2 = fp_mul(x_clamped, x_clamped);
    let num = 65536 + x_clamped + (x2 >> 1);
    let denom = 65536 - x_clamped + (x2 >> 1);
    (num << 16) / denom
}

#[inline(always)]
pub fn softmax_4_fixed(logits: &[f32; 4]) -> [f32; 4] {
    // Convert to fixed-point, 16.16 format
    let fp: [i64; 4] = [
        fp_from_float(logits[0]),
        fp_from_float(logits[1]),
        fp_from_float(logits[2]),
        fp_from_float(logits[3]),
    ];
    
    // Find max (branchless using arithmetic)
    let max01 = if fp[0] > fp[1] { fp[0] } else { fp[1] };
    let max23 = if fp[2] > fp[3] { fp[2] } else { fp[3] };
    let max_val = if max01 > max23 { max01 } else { max23 };
    
    // Subtract max and compute exp (unrolled)
    let e0 = fp_exp_approx(fp[0] - max_val);
    let e1 = fp_exp_approx(fp[1] - max_val);
    let e2 = fp_exp_approx(fp[2] - max_val);
    let e3 = fp_exp_approx(fp[3] - max_val);
    
    let sum = e0 + e1 + e2 + e3;
    let inv_sum = (1i64 << 32) / sum;
    
    [
        fp_to_float(fp_mul(e0, inv_sum)),
        fp_to_float(fp_mul(e1, inv_sum)),
        fp_to_float(fp_mul(e2, inv_sum)),
        fp_to_float(fp_mul(e3, inv_sum)),
    ]
}