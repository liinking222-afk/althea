use std::sync::atomic::{AtomicU64, AtomicUsize, Ordering};
use std::time::{SystemTime, UNIX_EPOCH};

const RING_SIZE: usize = 8192; // Power of 2 for bit-mask indexing
const MODULE_HASH_BITS: u64 = 16;
const MODULE_HASH_MASK: u64 = (1 << MODULE_HASH_BITS) - 1;

#[repr(C, align(64))] // Cache line aligned
struct TelemetryEntry {
    timestamp_us: AtomicU64,
    module_hash: AtomicU64,
    invocation_count: AtomicU64,
}

#[repr(C)]
pub struct ModuleTelemetryRing {
    entries: [TelemetryEntry; RING_SIZE],
    write_cursor: AtomicUsize,
    histogram: [AtomicU64; 1 << MODULE_HASH_BITS],
}

impl ModuleTelemetryRing {
    pub const fn new() -> Self {
        const ENTRY: TelemetryEntry = TelemetryEntry {
            timestamp_us: AtomicU64::new(0),
            module_hash: AtomicU64::new(0),
            invocation_count: AtomicU64::new(0),
        };
        const ZERO: AtomicU64 = AtomicU64::new(0);
        Self {
            entries: [ENTRY; RING_SIZE],
            write_cursor: AtomicUsize::new(0),
            histogram: [ZERO; 1 << MODULE_HASH_BITS],
        }
    }

    #[inline(always)]
    fn hash_module(name: &str) -> u64 {
        let mut h: u64 = 5381;
        for b in name.bytes() {
            h = h.wrapping_mul(33).wrapping_add(b as u64);
        }
        h & MODULE_HASH_MASK
    }

    #[inline(always)]
    pub fn record(&self, module_name: &str) {
        let now_us = SystemTime::now()
            .duration_since(UNIX_EPOCH)
            .unwrap()
            .as_micros() as u64;
        
        let hash = Self::hash_module(module_name);
        let idx = self.write_cursor.fetch_add(1, Ordering::Relaxed) & (RING_SIZE - 1);
        
        self.entries[idx].timestamp_us.store(now_us, Ordering::Relaxed);
        self.entries[idx].module_hash.store(hash, Ordering::Relaxed);
        self.histogram[hash as usize].fetch_add(1, Ordering::Relaxed);
    }

    #[inline(always)]
    pub fn frequency(&self, module_name: &str) -> u64 {
        let hash = Self::hash_module(module_name);
        self.histogram[hash as usize].load(Ordering::Relaxed)
    }

    pub fn top_modules(&self, buf: &mut [(u64, u64); 16]) -> usize {
        for i in 0..16 { buf[i] = (0, 0); }
        for (hash, count) in self.histogram.iter().enumerate() {
            let c = count.load(Ordering::Relaxed);
            if c > buf[15].1 {
                buf[15] = (hash as u64, c);
                buf.sort_unstable_by(|a, b| b.1.cmp(&a.1));
            }
        }
        buf.iter().position(|&(_, c)| c == 0).unwrap_or(16)
    }
}