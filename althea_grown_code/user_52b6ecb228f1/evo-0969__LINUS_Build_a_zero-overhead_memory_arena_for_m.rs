use std::alloc::{alloc, dealloc, Layout};
use std::ptr;

const ARENA_SIZE: usize = 1024 * 1024; // 1MB
const MODULE_SLOT_SIZE: usize = 256;
const MAX_MODULES: usize = ARENA_SIZE / MODULE_SLOT_SIZE;

#[repr(C, packed)]
struct ModuleRecord {
    hash: u64,
    timestamp: u64,
    invocation_count: u32,
    pattern_signature: [u8; 32],
    name_len: u8,
    name_data: [u8; 191],
}

pub struct ModuleArena {
    base: *mut u8,
    layout: Layout,
    next_slot: usize,
    index: [u16; 65536], // hash -> slot lookup
}

impl ModuleArena {
    pub fn new() -> Self {
        let layout = Layout::from_size_align(ARENA_SIZE, 64).unwrap();
        let base = unsafe { alloc(layout) };
        let mut index = [0xFFFF; 65536];
        
        Self {
            base,
            layout,
            next_slot: 0,
            index,
        }
    }

    pub fn insert(&mut self, hash: u64, pattern: &[u8; 32], name: &str) -> Option<usize> {
        if self.next_slot >= MAX_MODULES {
            return None;
        }

        let slot = self.next_slot;
        let offset = slot * MODULE_SLOT_SIZE;
        let record_ptr = unsafe { self.base.add(offset) as *mut ModuleRecord };
        
        let mut name_data = [0u8; 191];
        let copy_len = name.len().min(191);
        name_data[..copy_len].copy_from_slice(&name.as_bytes()[..copy_len]);

        unsafe {
            ptr::write(record_ptr, ModuleRecord {
                hash,
                timestamp: 0,
                invocation_count: 1,
                pattern_signature: *pattern,
                name_len: copy_len as u8,
                name_data,
            });
        }

        let index_key = (hash & 0xFFFF) as usize;
        self.index[index_key] = slot as u16;
        self.next_slot += 1;
        Some(slot)
    }

    pub fn lookup(&self, hash: u64) -> Option<&ModuleRecord> {
        let index_key = (hash & 0xFFFF) as usize;
        let slot = self.index[index_key];
        if slot == 0xFFFF {
            return None;
        }
        let offset = (slot as usize) * MODULE_SLOT_SIZE;
        Some(unsafe { &*(self.base.add(offset) as *const ModuleRecord) })
    }
}

impl Drop for ModuleArena {
    fn drop(&mut self) {
        unsafe { dealloc(self.base, self.layout); }
    }
}