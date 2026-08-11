use std::arch::x86_64::_mm_prefetch;
const CACHELINE: usize = 64;
const RING_SIZE: usize = 256; // power of 2 for mask-based wrap
const _MM_HINT_T0: i32 = 3;

#[repr(align(64))]
struct EventSlot {
    timestamp_ns: u64,
    module_hash: u64,     // xxhash3 of module name, 8 bytes
    dependency_bits: u32,  // 32 bits = 32 possible dependencies
    cache_misses: u16,    // predicted cache misses (0-65535)
    flags: u8,            // growth|evo|integration|seam
    _pad: u8,
}

#[repr(align(64))]
struct HotPathProfiler {
    ring: [EventSlot; RING_SIZE],
    head: usize,
    access_heatmap: [u32; RING_SIZE / 8], // 8 slots per u32 (4-bit counters)
}

impl HotPathProfiler {
    #[inline(always)]
    fn log_access(&mut self, module: &str, deps: u32, flags: u8) -> u16 {
        let hash = xxh3_64(module.as_bytes());
        let idx = self.head & (RING_SIZE - 1);
        
        // prefetch next cacheline
        unsafe {
            let next_idx = (idx + 1) & (RING_SIZE - 1);
            _mm_prefetch(
                &self.ring[next_idx] as *const _ as *const i8,
                _MM_HINT_T0
            );
        }
        
        // compute cache misses via dependency hamming distance
        let prev_idx = (idx.wrapping_sub(1)) & (RING_SIZE - 1);
        let misses = (deps ^ self.ring[prev_idx].dependency_bits).count_ones() as u16;
        
        self.ring[idx] = EventSlot {
            timestamp_ns: rdtsc(),
            module_hash: hash,
            dependency_bits: deps,
            cache_misses: misses,
            flags,
            _pad: 0,
        };
        
        // update heatmap (4-bit saturating counter)
        let heat_idx = idx / 8;
        let shift = (idx % 8) * 4;
        let counter = (self.access_heatmap[heat_idx] >> shift) & 0xF;
        if counter < 15 {
            self.access_heatmap[heat_idx] += 1 << shift;
        }
        
        self.head = self.head.wrapping_add(1);
        misses
    }
}

#[inline(always)]
fn xxh3_64(data: &[u8]) -> u64 {
    const PRIME64_1: u64 = 0x9E3779B185EBCA87;
    let mut h = PRIME64_1;
    for &b in data { h = h.rotate_left(13).wrapping_mul(PRIME64_1) ^ (b as u64); }
    h
}

#[inline(always)]
fn rdtsc() -> u64 { unsafe { std::arch::x86_64::_rdtsc() } }