use std::collections::HashMap;
use std::hash::{Hash, Hasher};
use std::collections::hash_map::DefaultHasher;

const ARENA_SIZE: usize = 4096;
const SLOT_MASK: usize = ARENA_SIZE - 1;

#[repr(C)]
struct ContextPointer {
    hash: u64,
    generation: u32,
    ref_count: u16,
    flags: u16,
}

pub struct MemoryArena {
    slots: [Option<ContextPointer>; ARENA_SIZE],
    generation: u32,
    active_count: usize,
}

impl MemoryArena {
    pub fn new() -> Self {
        Self {
            slots: [None; ARENA_SIZE],
            generation: 0,
            active_count: 0,
        }
    }

    #[inline]
    fn compute_hash(fragment: &str) -> u64 {
        let mut hasher = DefaultHasher::new();
        fragment.hash(&mut hasher);
        hasher.finish()
    }

    pub fn register(&mut self, fragment: &str) -> bool {
        let hash = Self::compute_hash(fragment);
        let mut slot = (hash as usize) & SLOT_MASK;
        
        for _ in 0..16 {
            match &mut self.slots[slot] {
                None => {
                    self.slots[slot] = Some(ContextPointer {
                        hash,
                        generation: self.generation,
                        ref_count: 1,
                        flags: 0,
                    });
                    self.active_count += 1;
                    return true;
                }
                Some(ptr) if ptr.hash == hash => {
                    ptr.ref_count = ptr.ref_count.saturating_add(1);
                    return false;
                }
                _ => slot = (slot + 1) & SLOT_MASK,
            }
        }
        false
    }

    pub fn sweep_generation(&mut self) {
        self.generation += 1;
        let cutoff = self.generation.saturating_sub(2);
        
        for slot in &mut self.slots {
            if let Some(ptr) = slot {
                if ptr.generation < cutoff && ptr.ref_count == 0 {
                    *slot = None;
                    self.active_count -= 1;
                }
            }
        }
    }

    pub fn is_duplicate(&self, fragment: &str) -> bool {
        let hash = Self::compute_hash(fragment);
        let mut slot = (hash as usize) & SLOT_MASK;
        
        for _ in 0..16 {
            match &self.slots[slot] {
                Some(ptr) if ptr.hash == hash => return true,
                None => return false,
                _ => slot = (slot + 1) & SLOT_MASK,
            }
        }
        false
    }
}