use std::sync::atomic::{AtomicU64, AtomicUsize, Ordering};
use std::time::{SystemTime, UNIX_EPOCH};

const RING_SIZE: usize = 4096;
const MODULE_NAME_MAX: usize = 64;

#[repr(C, align(64))]
struct InvocationRecord {
    timestamp_us: AtomicU64,
    module_id_hash: AtomicU64,
    name_bytes: [u8; MODULE_NAME_MAX],
}

impl InvocationRecord {
    const fn new() -> Self {
        Self {
            timestamp_us: AtomicU64::new(0),
            module_id_hash: AtomicU64::new(0),
            name_bytes: [0u8; MODULE_NAME_MAX],
        }
    }
}

pub struct InvocationArena {
    ring: [InvocationRecord; RING_SIZE],
    head: AtomicUsize,
}

impl InvocationArena {
    pub const fn new() -> Self {
        const RECORD: InvocationRecord = InvocationRecord::new();
        Self {
            ring: [RECORD; RING_SIZE],
            head: AtomicUsize::new(0),
        }
    }

    #[inline]
    pub fn record(&self, module_name: &str) {
        let idx = self.head.fetch_add(1, Ordering::Relaxed) & (RING_SIZE - 1);
        let record = &self.ring[idx];
        
        let now = SystemTime::now()
            .duration_since(UNIX_EPOCH)
            .unwrap()
            .as_micros() as u64;
        
        record.timestamp_us.store(now, Ordering::Relaxed);
        record.module_id_hash.store(hash_djb2(module_name), Ordering::Relaxed);
    }

    pub fn decay_scan(&self, window_us: u64) -> Vec<(u64, u32)> {
        let now = SystemTime::now()
            .duration_since(UNIX_EPOCH)
            .unwrap()
            .as_micros() as u64;
        
        let mut freq_map = std::collections::HashMap::new();
        let cutoff = now.saturating_sub(window_us);
        
        for record in &self.ring {
            let ts = record.timestamp_us.load(Ordering::Relaxed);
            if ts > cutoff && ts <= now {
                let hash = record.module_id_hash.load(Ordering::Relaxed);
                *freq_map.entry(hash).or_insert(0u32) += 1;
            }
        }
        
        freq_map.into_iter().collect()
    }
}

#[inline]
fn hash_djb2(s: &str) -> u64 {
    s.bytes().fold(5381u64, |h, b| h.wrapping_mul(33).wrapping_add(b as u64))
}

static ARENA: InvocationArena = InvocationArena::new();

pub fn track(module: &str) { ARENA.record(module); }
pub fn scan(window_us: u64) -> Vec<(u64, u32)> { ARENA.decay_scan(window_us) }