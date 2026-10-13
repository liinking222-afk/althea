#![allow(unused)]
use std::arch::x86_64::*;

#[repr(C, align(64))] // Cache-line aligned for hot loop access
pub struct MetricTensor {
    g: [f64; 16],      // 4x4 metric components, row-major
    g_inv: [f64; 16],  // Inverse metric, pre-computed
    christoffel: [f64; 64], // Γ^μ_νρ symbols (4x4x4), inline computed
}

impl MetricTensor {
    #[inline(always)]
    pub fn flrw(a: f64, k: f64) -> Self {
        // FLRW metric: ds² = -dt² + a²(t)[dr²/(1-kr²) + r²dΩ²]
        // Simplified: diag(-1, a², a², a²) for flat k=0
        let a2 = a * a;
        let mut g = [0.0; 16];
        g[0] = -1.0; g[5] = a2; g[10] = a2; g[15] = a2;
        
        let mut g_inv = [0.0; 16];
        g_inv[0] = -1.0; g_inv[5] = 1.0/a2; g_inv[10] = 1.0/a2; g_inv[15] = 1.0/a2;
        
        let mut m = MetricTensor { g, g_inv, christoffel: [0.0; 64] };
        m.compute_christoffel_inline(a);
        m
    }
    
    #[inline(always)]
    fn compute_christoffel_inline(&mut self, a: f64) {
        // Γ^t_ij = (ȧ/a)δ_ij for spatial indices (hot path: 9 ops)
        // Γ^i_tj = (ȧ/a)δ^i_j for i,j spatial
        let h = a / (a * a); // ȧ/a ~ H(a) approximation (1/a for matter-dom)
        
        for i in 1..4 {
            for j in 1..4 {
                let idx = 0 * 16 + i * 4 + j; // Γ^0_ij
                self.christoffel[idx] = if i == j { h * self.g[i*4+i] } else { 0.0 };
                
                let idx2 = i * 16 + 0 * 4 + j; // Γ^i_0j
                self.christoffel[idx2] = if i == j { h } else { 0.0 };
            }
        }
    }
    
    #[inline(always)]
    pub fn eos_w(&self, rho: f64, p: f64) -> f64 {
        // w = p/ρ (equation of state), branch-free
        p / (rho + 1e-100) // Avoid div-by-zero without branching
    }
    
    #[inline(always)]
    pub fn evolve_w_step(&self, w0: f64, wa: f64, a: f64) -> f64 {
        // w(a) = w0 + wa(1-a) parametrization, 3 FLOPs
        w0 + wa * (1.0 - a)
    }
}

#[inline(never)]
pub fn batch_eos_trajectory(a_arr: &[f64], w0: f64, wa: f64, out: &mut [f64]) {
    // Hot loop: vectorizable, no allocation, cache-sequential
    for (i, &a) in a_arr.iter().enumerate() {
        let m = MetricTensor::flrw(a, 0.0);
        out[i] = m.evolve_w_step(w0, wa, a); // Inline expansion
    }
}