use std::arch::x86_64::_rdtsc;
use std::sync::atomic::{AtomicU64, Ordering};

const MAX_MODULES: usize = 256;
const CACHE_LINE: usize = 64;

#[repr(align(64))]
struct ModuleStats {
    call_count: AtomicU64,
    total_cycles: AtomicU64,
    min_cycles: AtomicU64,
    max_cycles: AtomicU64,
    _pad: [u8; 32], // pad to cache line
}

pub struct HotLoopProfiler {
    stats: Box<[ModuleStats; MAX_MODULES]>,
    active_slots: AtomicU64,
}

impl HotLoopProfiler {
    #[inline(always)]
    pub fn new() -> Self {
        let stats = unsafe {
            let layout = std::alloc::Layout::new::<[ModuleStats; MAX_MODULES]>();
            let ptr = std::alloc::alloc_zeroed(layout) as *mut [ModuleStats; MAX_MODULES];
            Box::from_raw(ptr)
        };
        Self { stats, active_slots: AtomicU64::new(0) }
    }

    #[inline(always)]
    pub fn enter(&self, slot: u8) -> u64 {
        unsafe { _rdtsc() }
    }

    #[inline(always)]
    pub fn exit(&self, slot: u8, start: u64) {
        let cycles = unsafe { _rdtsc() } - start;
        let s = &self.stats[slot as usize];
        
        s.call_count.fetch_add(1, Ordering::Relaxed);
        s.total_cycles.fetch_add(cycles, Ordering::Relaxed);
        
        let mut min = s.min_cycles.load(Ordering::Relaxed);
        while cycles < min || min == 0 {
            match s.min_cycles.compare_exchange_weak(min, cycles, Ordering::Relaxed, Ordering::Relaxed) {
                Ok(_) => break,
                Err(x) => min = x,
            }
        }
        
        let mut max = s.max_cycles.load(Ordering::Relaxed);
        while cycles > max {
            match s.max_cycles.compare_exchange_weak(max, cycles, Ordering::Relaxed, Ordering::Relaxed) {
                Ok(_) => break,
                Err(x) => max = x,
            }
        }
    }

    #[inline(always)]
    pub fn report(&self, slot: u8) -> (u64, u64, u64, u64) {
        let s = &self.stats[slot as usize];
        (s.call_count.load(Ordering::Relaxed),
         s.total_cycles.load(Ordering::Relaxed),
         s.min_cycles.load(Ordering::Relaxed),
         s.max_cycles.load(Ordering::Relaxed))
    }
}