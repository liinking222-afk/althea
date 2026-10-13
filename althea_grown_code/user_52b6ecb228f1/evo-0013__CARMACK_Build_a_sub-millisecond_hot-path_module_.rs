// cache-aligned module router - zero allocation hot path
// inline everything, branch predict friendly, 64-byte cache lines
use std::sync::atomic::{AtomicU64, Ordering};

#[repr(align(64))]
pub struct ModuleRouter {
    dispatch: [Option<fn(&[u8]) -> u32>; 256], // flat array, predictable access
    stats: [AtomicU64; 256],                    // cycle counters, same cache line
    bitmap: [u64; 4],                           // 256 bits for active modules
}

impl ModuleRouter {
    #[inline(always)]
    pub const fn new() -> Self {
        const NONE: Option<fn(&[u8]) -> u32> = None;
        const ZERO: AtomicU64 = AtomicU64::new(0);
        Self {
            dispatch: [NONE; 256],
            stats: [ZERO; 256],
            bitmap: [0; 4],
        }
    }

    #[inline(always)]
    pub fn register(&mut self, id: u8, handler: fn(&[u8]) -> u32) {
        let idx = id as usize;
        self.dispatch[idx] = Some(handler);
        self.bitmap[idx >> 6] |= 1u64 << (idx & 63); // set bit
    }

    #[inline(always)]
    pub fn is_active(&self, id: u8) -> bool {
        let idx = id as usize;
        (self.bitmap[idx >> 6] & (1u64 << (idx & 63))) != 0
    }

    #[inline(always)] // HOT PATH - no bounds check, caller guarantees validity
    pub unsafe fn route_unchecked(&self, id: u8, input: &[u8]) -> u32 {
        let idx = id as usize;
        let start = Self::rdtsc();
        let result = self.dispatch.get_unchecked(idx).unwrap_unchecked()(input);
        let cycles = Self::rdtsc() - start;
        self.stats.get_unchecked(idx).fetch_add(cycles, Ordering::Relaxed);
        result
    }

    #[inline(always)]
    pub fn route(&self, id: u8, input: &[u8]) -> Option<u32> {
        if !self.is_active(id) { return None; }
        Some(unsafe { self.route_unchecked(id, input) })
    }

    #[inline(always)]
    fn rdtsc() -> u64 {
        #[cfg(target_arch = "x86_64")]
        unsafe { core::arch::x86_64::_rdtsc() }
        #[cfg(not(target_arch = "x86_64"))]
        0 // fallback
    }

    #[inline(always)]
    pub fn cycles(&self, id: u8) -> u64 {
        self.stats[id as usize].load(Ordering::Relaxed)
    }
}

// Example cognitive module handlers - inline candidate
#[inline(always)]
fn valence_redistribute(input: &[u8]) -> u32 {
    input.iter().fold(0u32, |acc, &b| acc.wrapping_add(b as u32 * 0x9e3779b9))
}

#[inline(always)]
fn narrative_bifurcate(input: &[u8]) -> u32 {
    (input.len() as u32).wrapping_mul(0xcc9e2d51).rotate_left(15)
}