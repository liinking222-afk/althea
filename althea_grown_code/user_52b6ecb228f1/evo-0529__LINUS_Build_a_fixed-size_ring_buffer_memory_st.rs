use std::sync::atomic::{AtomicUsize, Ordering};
use std::time::SystemTime;

const RING_SIZE: usize = 256;

#[repr(C)]
#[derive(Clone, Copy)]
struct ModuleRecord {
    timestamp: u64,
    module_id: u64,
    pattern_hash: u64,
    invocation_count: u32,
    token_cost: u32,
}

impl Default for ModuleRecord {
    fn default() -> Self {
        Self {
            timestamp: 0,
            module_id: 0,
            pattern_hash: 0,
            invocation_count: 0,
            token_cost: 0,
        }
    }
}

pub struct ModuleMemoryRing {
    buffer: [ModuleRecord; RING_SIZE],
    head: AtomicUsize,
}

impl ModuleMemoryRing {
    pub const fn new() -> Self {
        Self {
            buffer: [ModuleRecord {
                timestamp: 0,
                module_id: 0,
                pattern_hash: 0,
                invocation_count: 0,
                token_cost: 0,
            }; RING_SIZE],
            head: AtomicUsize::new(0),
        }
    }

    pub fn push(&mut self, module_id: u64, pattern_hash: u64, token_cost: u32) {
        let idx = self.head.fetch_add(1, Ordering::Relaxed) % RING_SIZE;
        let timestamp = SystemTime::now()
            .duration_since(SystemTime::UNIX_EPOCH)
            .unwrap()
            .as_secs();
        
        self.buffer[idx] = ModuleRecord {
            timestamp,
            module_id,
            pattern_hash,
            invocation_count: 1,
            token_cost,
        };
    }

    pub fn find_pattern(&self, pattern_hash: u64) -> Option<&ModuleRecord> {
        self.buffer.iter().rev()
            .find(|r| r.pattern_hash == pattern_hash && r.timestamp > 0)
    }

    pub fn last_n(&self, n: usize) -> impl Iterator<Item = &ModuleRecord> {
        let count = self.head.load(Ordering::Relaxed).min(RING_SIZE);
        self.buffer[..count].iter().rev().take(n)
    }
}