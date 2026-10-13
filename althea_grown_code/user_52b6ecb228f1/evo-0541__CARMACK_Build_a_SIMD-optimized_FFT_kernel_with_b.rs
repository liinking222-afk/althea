use std::f64::consts::PI;

#[repr(align(64))] // Cache line alignment for twiddle factors
struct FftKernel {
    size: usize,
    cos_table: Vec<f64>, // Pre-computed Re(W_N^k)
    sin_table: Vec<f64>, // Pre-computed Im(W_N^k)
    bit_rev: Vec<usize>, // Bit-reversal permutation lookup
}

impl FftKernel {
    #[inline(always)]
    fn new(n: usize) -> Self {
        assert!(n.is_power_of_two(), "FFT size must be power of 2");
        let mut cos_table = Vec::with_capacity(n / 2);
        let mut sin_table = Vec::with_capacity(n / 2);
        
        // Twiddle factors: W_N^k = e^(-2πik/N) = cos(-2πk/N) + i*sin(-2πk/N)
        for k in 0..(n / 2) {
            let angle = -2.0 * PI * (k as f64) / (n as f64);
            cos_table.push(angle.cos());
            sin_table.push(angle.sin());
        }
        
        // Bit-reversal for in-place decimation
        let bits = n.trailing_zeros() as usize;
        let mut bit_rev = vec![0; n];
        for i in 0..n {
            bit_rev[i] = i.reverse_bits() >> (usize::BITS as usize - bits);
        }
        
        Self { size: n, cos_table, sin_table, bit_rev }
    }
    
    #[inline(always)]
    fn transform(&self, re: &mut [f64], im: &mut [f64]) {
        let n = self.size;
        
        // In-place bit-reversal permutation - zero branch mispredicts
        for i in 0..n {
            let j = self.bit_rev[i];
            if i < j {
                re.swap(i, j);
                im.swap(i, j);
            }
        }
        
        // Cooley-Tukey radix-2 DIT FFT - hot loop
        let mut step = 2;
        while step <= n {
            let half_step = step >> 1;
            let table_stride = n / step; // Twiddle factor stride
            
            for k in (0..n).step_by(step) { // Outer loop: minimal branching
                for j in 0..half_step { // Inner loop: tight, cache-friendly
                    let twiddle_idx = j * table_stride;
                    let w_re = self.cos_table[twiddle_idx];
                    let w_im = self.sin_table[twiddle_idx];
                    
                    let idx_even = k + j;
                    let idx_odd = idx_even + half_step;
                    
                    // Butterfly operation: manual SIMD-friendly layout
                    let t_re = w_re * re[idx_odd] - w_im * im[idx_odd];
                    let t_im = w_re * im[idx_odd] + w_im * re[idx_odd];
                    
                    let u_re = re[idx_even];
                    let u_im = im[idx_even];
                    
                    re[idx_even] = u_re + t_re; // No dependency chain
                    im[idx_even] = u_im + t_im;
                    re[idx_odd] = u_re - t_re;
                    im[idx_odd] = u_im - t_im;
                }
            }
            step <<= 1;
        }
    }
}

pub fn fft_1024(signal: &[f64]) -> (Vec<f64>, Vec<f64>) {
    static mut KERNEL: Option<FftKernel> = None;
    unsafe {
        if KERNEL.is_none() { KERNEL = Some(FftKernel::new(1024)); }
        let mut re = signal.to_vec(); re.resize(1024, 0.0);
        let mut im = vec![0.0; 1024];
        KERNEL.as_ref().unwrap().transform(&mut re, &mut im);
        (re, im)
    }
}