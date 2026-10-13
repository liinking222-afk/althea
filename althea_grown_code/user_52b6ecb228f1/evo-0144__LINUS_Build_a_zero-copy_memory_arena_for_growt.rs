use std::alloc::{alloc, dealloc, Layout};
use std::ptr;

const MODULE_SLOTS: usize = 256;
const NAME_LEN: usize = 48;
const META_LEN: usize = 128;

#[repr(C, packed)]
struct ModuleSlot {
    active: u8,
    timestamp: u64,
    invocations: u32,
    name: [u8; NAME_LEN],
    metadata: [u8; META_LEN],
}

pub struct ModuleArena {
    base: *mut ModuleSlot,
    layout: Layout,
    count: usize,
}

impl ModuleArena {
    pub fn new() -> Self {
        let layout = Layout::array::<ModuleSlot>(MODULE_SLOTS).unwrap();
        let base = unsafe { alloc(layout) as *mut ModuleSlot };
        unsafe { ptr::write_bytes(base, 0, MODULE_SLOTS) };
        ModuleArena { base, layout, count: 0 }
    }

    pub fn allocate(&mut self, name: &[u8], meta: &[u8]) -> Option<usize> {
        if self.count >= MODULE_SLOTS { return None; }
        
        let slot = unsafe { self.base.add(self.count) };
        let mut s = ModuleSlot {
            active: 1,
            timestamp: self.count as u64,
            invocations: 0,
            name: [0; NAME_LEN],
            metadata: [0; META_LEN],
        };
        
        let nlen = name.len().min(NAME_LEN);
        s.name[..nlen].copy_from_slice(&name[..nlen]);
        let mlen = meta.len().min(META_LEN);
        s.metadata[..mlen].copy_from_slice(&meta[..mlen]);
        
        unsafe { ptr::write(slot, s) };
        self.count += 1;
        Some(self.count - 1)
    }

    pub fn get(&self, idx: usize) -> Option<(*const u8, *const u8)> {
        if idx >= self.count { return None; }
        unsafe {
            let slot = self.base.add(idx);
            if (*slot).active == 0 { return None; }
            Some(((*slot).name.as_ptr(), (*slot).metadata.as_ptr()))
        }
    }

    pub fn increment(&mut self, idx: usize) {
        if idx < self.count {
            unsafe { (*self.base.add(idx)).invocations += 1; }
        }
    }

    pub fn scan_hot(&self, threshold: u32) -> Vec<usize> {
        let mut hot = Vec::with_capacity(32);
        for i in 0..self.count {
            unsafe {
                if (*self.base.add(i)).invocations >= threshold {
                    hot.push(i);
                }
            }
        }
        hot
    }
}

impl Drop for ModuleArena {
    fn drop(&mut self) {
        unsafe { dealloc(self.base as *mut u8, self.layout) };
    }
}