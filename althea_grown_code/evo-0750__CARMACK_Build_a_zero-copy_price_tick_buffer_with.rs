#![no_std]
use core::arch::x86_64::*;

#[repr(C, align(32))]
pub struct TickBuffer {
    prices: [f32; 256],    // power-of-2 for mask ops, AVX-aligned
    sizes: [f32; 256],
    timestamps: [u64; 256],
    head: u8,              // wraps at 256 automatically
}

impl TickBuffer {
    #[inline(always)]
    pub const fn new() -> Self {
        Self {
            prices: [0.0; 256],
            sizes: [0.0; 256],
            timestamps: [0; 256],
            head: 0,
        }
    }

    #[inline(always)]
    pub fn push(&mut self, price: f32, size: f32, ts: u64) {
        let idx = self.head as usize;
        unsafe {
            *self.prices.get_unchecked_mut(idx) = price;
            *self.sizes.get_unchecked_mut(idx) = size;
            *self.timestamps.get_unchecked_mut(idx) = ts;
        }
        self.head = self.head.wrapping_add(1); // branchless wrap
    }

    #[inline(always)]
    pub unsafe fn vwap_last_n(&self, n: u8) -> f32 {
        let n = n.min(256) as usize;
        let mut sum_pv: f32 = 0.0;
        let mut sum_v: f32 = 0.0;
        
        // Unroll 8x for pipeline depth
        let chunks = n / 8;
        for i in 0..chunks {
            let base = (self.head.wrapping_sub(n as u8) as usize + i * 8) & 0xFF;
            for j in 0..8 {
                let idx = (base + j) & 0xFF;
                let p = *self.prices.get_unchecked(idx);
                let v = *self.sizes.get_unchecked(idx);
                sum_pv += p * v;
                sum_v += v;
            }
        }
        
        // Handle remainder without branching
        for i in (chunks * 8)..n {
            let idx = (self.head.wrapping_sub((n - i) as u8) as usize) & 0xFF;
            let p = *self.prices.get_unchecked(idx);
            let v = *self.sizes.get_unchecked(idx);
            sum_pv += p * v;
            sum_v += v;
        }
        
        sum_pv / sum_v.max(1e-9) // no div-by-zero, no branch
    }

    #[inline(always)]
    pub fn spread(&self) -> f32 {
        unsafe {
            let last = *self.prices.get_unchecked((self.head.wrapping_sub(1)) as usize);
            let prev = *self.prices.get_unchecked((self.head.wrapping_sub(2)) as usize);
            last - prev
        }
    }
}