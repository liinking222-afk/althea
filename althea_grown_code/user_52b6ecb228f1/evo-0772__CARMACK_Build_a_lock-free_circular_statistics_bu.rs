use std::sync::atomic::{AtomicU64, AtomicUsize, Ordering};
use std::arch::x86_64::*;

const RING_SIZE: usize = 4096; // power of 2 for mask
const RING_MASK: usize = RING_SIZE - 1;

#[repr(align(64))] // cache line alignment
pub struct PerfRing {
    head: AtomicUsize,
    samples: [AtomicU64; RING_SIZE],
    sum_cache: AtomicU64,
    sum_sq_cache: AtomicU64,
}

impl PerfRing {
    pub const fn new() -> Self {
        const ZERO: AtomicU64 = AtomicU64::new(0);
        Self {
            head: AtomicUsize::new(0),
            samples: [ZERO; RING_SIZE],
            sum_cache: AtomicU64::new(0),
            sum_sq_cache: AtomicU64::new(0),
        }
    }

    #[inline(always)]
    pub fn push(&self, nanos: u64) {
        let idx = self.head.fetch_add(1, Ordering::Relaxed) & RING_MASK;
        let old = self.samples[idx].swap(nanos, Ordering::Relaxed);
        
        // incremental cache update - O(1) not O(n)
        self.sum_cache.fetch_add(nanos, Ordering::Relaxed);
        self.sum_cache.fetch_sub(old, Ordering::Relaxed);
        self.sum_sq_cache.fetch_add(nanos * nanos, Ordering::Relaxed);
        self.sum_sq_cache.fetch_sub(old * old, Ordering::Relaxed);
    }

    #[inline(always)]
    pub fn mean_nanos(&self) -> f64 {
        let sum = self.sum_cache.load(Ordering::Relaxed);
        (sum as f64) / (RING_SIZE as f64)
    }

    #[inline(always)]
    pub fn variance_nanos(&self) -> f64 {
        let sum = self.sum_cache.load(Ordering::Relaxed) as f64;
        let sum_sq = self.sum_sq_cache.load(Ordering::Relaxed) as f64;
        let n = RING_SIZE as f64;
        (sum_sq / n) - (sum / n).powi(2)
    }

    #[inline(always)]
    pub fn stddev_nanos(&self) -> f64 {
        self.variance_nanos().sqrt()
    }

    // hot path: single-cycle percentile approximation via histogram
    #[inline(always)]
    pub fn p99_fast(&self) -> u64 {
        let mut buckets = [0u32; 64]; // log2 buckets
        for i in 0..RING_SIZE {
            let val = self.samples[i].load(Ordering::Relaxed);
            if val > 0 {
                let bucket = 63 - val.leading_zeros() as usize;
                buckets[bucket] += 1;
            }
        }
        let p99_count = (RING_SIZE * 99) / 100;
        let mut acc = 0u32;
        for (bucket, &count) in buckets.iter().enumerate() {
            acc += count;
            if acc >= p99_count as u32 {
                return 1u64 << bucket;
            }
        }
        0
    }
}