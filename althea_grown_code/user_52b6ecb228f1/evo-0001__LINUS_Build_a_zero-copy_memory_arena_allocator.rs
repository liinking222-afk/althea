use std::alloc::{alloc, dealloc, Layout};
use std::ptr::NonNull;
use std::sync::atomic::{AtomicUsize, Ordering};

const ARENA_SIZE: usize = 16 * 1024 * 1024; // 16MB per arena
const SNAPSHOT_SLOTS: usize = 64; // Power of 2 for fast modulo

#[repr(C)]
struct Snapshot {
    offset: usize,
    size: usize,
    generation: u64,
}

pub struct CognitiveArena {
    base: NonNull<u8>,
    cursor: AtomicUsize,
    snapshots: [Snapshot; SNAPSHOT_SLOTS],
    snap_head: AtomicUsize,
    generation: AtomicUsize,
}

impl CognitiveArena {
    pub fn new() -> Self {
        unsafe {
            let layout = Layout::from_size_align_unchecked(ARENA_SIZE, 64);
            let base = NonNull::new(alloc(layout)).expect("allocation failed");
            
            CognitiveArena {
                base,
                cursor: AtomicUsize::new(0),
                snapshots: [Snapshot { offset: 0, size: 0, generation: 0 }; SNAPSHOT_SLOTS],
                snap_head: AtomicUsize::new(0),
                generation: AtomicUsize::new(1),
            }
        }
    }

    pub fn snapshot(&mut self) -> u64 {
        let cursor = self.cursor.load(Ordering::Acquire);
        let gen = self.generation.fetch_add(1, Ordering::Release);
        let slot = self.snap_head.fetch_add(1, Ordering::Release) & (SNAPSHOT_SLOTS - 1);
        
        self.snapshots[slot] = Snapshot {
            offset: cursor,
            size: cursor,
            generation: gen,
        };
        gen
    }

    pub fn rollback(&mut self, generation: u64) -> bool {
        for snap in &self.snapshots {
            if snap.generation == generation {
                self.cursor.store(snap.offset, Ordering::Release);
                return true;
            }
        }
        false
    }

    pub fn alloc_state(&self, size: usize) -> Option<NonNull<u8>> {
        let aligned = (size + 7) & !7;
        let offset = self.cursor.fetch_add(aligned, Ordering::AcqRel);
        
        if offset + aligned > ARENA_SIZE {
            return None;
        }
        
        unsafe { Some(NonNull::new_unchecked(self.base.as_ptr().add(offset))) }
    }

    pub fn reset(&mut self) {
        self.cursor.store(0, Ordering::Release);
        self.snap_head.store(0, Ordering::Release);
    }
}

impl Drop for CognitiveArena {
    fn drop(&mut self) {
        unsafe {
            let layout = Layout::from_size_align_unchecked(ARENA_SIZE, 64);
            dealloc(self.base.as_ptr(), layout);
        }
    }
}