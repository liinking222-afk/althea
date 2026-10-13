use std::sync::atomic::{AtomicUsize, Ordering};
use std::time::Instant;

const TRACE_SIZE: usize = 8192;
const MODULE_NAME_MAX: usize = 32;

#[repr(C, align(64))]
#[derive(Copy, Clone)]
struct TraceEntry {
    timestamp_ns: u64,
    module_id: u32,
    depth: u16,
    flags: u16,
    module_name: [u8; MODULE_NAME_MAX],
}

impl Default for TraceEntry {
    fn default() -> Self {
        Self {
            timestamp_ns: 0,
            module_id: 0,
            depth: 0,
            flags: 0,
            module_name: [0; MODULE_NAME_MAX],
        }
    }
}

pub struct TraceRing {
    buffer: [TraceEntry; TRACE_SIZE],
    head: AtomicUsize,
    start: Instant,
}

impl TraceRing {
    pub fn new() -> Self {
        Self {
            buffer: [TraceEntry::default(); TRACE_SIZE],
            head: AtomicUsize::new(0),
            start: Instant::now(),
        }
    }

    #[inline(always)]
    pub fn push(&mut self, module: &str, depth: u16, failed: bool) {
        let idx = self.head.fetch_add(1, Ordering::Relaxed) & (TRACE_SIZE - 1);
        let entry = &mut self.buffer[idx];
        
        entry.timestamp_ns = self.start.elapsed().as_nanos() as u64;
        entry.module_id = fxhash32(module.as_bytes());
        entry.depth = depth;
        entry.flags = if failed { 1 } else { 0 };
        
        let len = module.len().min(MODULE_NAME_MAX);
        entry.module_name[..len].copy_from_slice(&module.as_bytes()[..len]);
    }

    pub fn detect_seams(&self) -> Vec<(u32, u32)> {
        let mut failures = [0u16; 256];
        let snapshot_head = self.head.load(Ordering::Relaxed);
        let start = snapshot_head.saturating_sub(TRACE_SIZE);
        
        for i in start..snapshot_head {
            let entry = &self.buffer[i & (TRACE_SIZE - 1)];
            if entry.flags & 1 != 0 {
                let hash = (entry.module_id as usize) & 0xFF;
                failures[hash] = failures[hash].saturating_add(1);
            }
        }
        
        failures.iter().enumerate()
            .filter(|(_, &count)| count > 3)
            .map(|(idx, &count)| (idx as u32, count as u32))
            .collect()
    }
}

#[inline(always)]
fn fxhash32(bytes: &[u8]) -> u32 {
    let mut hash = 0x9e3779b9u32;
    for &b in bytes {
        hash = hash.rotate_left(5).wrapping_add(b as u32);
    }
    hash
}