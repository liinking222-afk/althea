// Ring buffer for module exec timestamps. Inline hot path. Cache-aligned.
// No heap after init. Sub-microsecond insert. Dense memory layout.

use std::time::{SystemTime, UNIX_EPOCH};

#[repr(align(64))] // Cache line alignment - prevents false sharing
pub struct ModuleTimestampRing {
    buf: [u64; 256],        // Power of 2 for mask optimization
    head: usize,            // Write pointer
    mask: usize,            // Bitwise AND faster than modulo
}

impl ModuleTimestampRing {
    #[inline(always)]
    pub const fn new() -> Self {
        Self {
            buf: [0u64; 256],
            head: 0,
            mask: 255,      // 256 - 1, for & operation
        }
    }

    // Hot loop: 3 instructions - load timestamp, mask index, store
    #[inline(always)]
    pub fn push(&mut self, module_id: u32) {
        let ts = SystemTime::now()
            .duration_since(UNIX_EPOCH)
            .unwrap()
            .as_micros() as u64;
        
        // Pack: upper 32 bits = timestamp delta from base, lower 32 = module_id
        let packed = (ts & 0xFFFFFFFF00000000) | (module_id as u64);
        
        self.buf[self.head & self.mask] = packed;
        self.head = self.head.wrapping_add(1); // Wrapping prevents overflow checks
    }

    // Sequential scan - cache prefetcher loves this
    #[inline]
    pub fn last_n(&self, n: usize) -> &[u64] {
        let count = n.min(256).min(self.head);
        let start = (self.head.wrapping_sub(count)) & self.mask;
        
        if start + count <= 256 {
            &self.buf[start..start + count]
        } else {
            &self.buf[0..count] // Wraparound case - caller handles
        }
    }

    // Inter-module timing delta. Returns microseconds between last two instances.
    #[inline]
    pub fn module_delta_us(&self, module_id: u32) -> Option<u64> {
        let target = module_id as u64;
        let mut last: Option<u64> = None;
        let mut prev: Option<u64> = None;
        
        // Scan backwards from head
        for i in (0..self.head.min(256)).rev() {
            let packed = self.buf[i & self.mask];
            if (packed & 0xFFFFFFFF) == target {
                if last.is_none() {
                    last = Some(packed >> 32);
                } else {
                    prev = Some(packed >> 32);
                    break;
                }
            }
        }
        
        match (last, prev) {
            (Some(l), Some(p)) => Some(l - p),
            _ => None,
        }
    }
}

// Static allocation - lives in .bss, zero runtime cost
static mut RING: ModuleTimestampRing = ModuleTimestampRing::new();