use std::sync::atomic::{AtomicU64, Ordering};
use std::alloc::{alloc, dealloc, Layout};
use std::ptr;

const RING_SIZE: usize = 4096; // power-of-2 for bitwise AND mask
const RING_MASK: usize = RING_SIZE - 1;

#[repr(C, align(64))] // cache-line aligned to prevent false sharing
struct CognitiveEvent {
    module_id: u32,
    timestamp_ns: u64,
    weight: f32,
    flags: u32,
}

#[repr(C)]
struct LockFreeRing {
    buffer: *mut CognitiveEvent,
    head: AtomicU64, // producer index, cache-aligned on own line
    _pad1: [u8; 56],
    tail: AtomicU64, // consumer index, cache-aligned on own line
    _pad2: [u8; 56],
}

impl LockFreeRing {
    fn new() -> Self {
        let layout = Layout::array::<CognitiveEvent>(RING_SIZE).unwrap();
        let buffer = unsafe { alloc(layout) as *mut CognitiveEvent };
        
        Self {
            buffer,
            head: AtomicU64::new(0),
            _pad1: [0; 56],
            tail: AtomicU64::new(0),
            _pad2: [0; 56],
        }
    }

    #[inline(always)]
    fn push(&self, event: CognitiveEvent) -> bool {
        let head = self.head.load(Ordering::Relaxed);
        let next_head = head.wrapping_add(1);
        let tail = self.tail.load(Ordering::Acquire);
        
        // full check: wrapping arithmetic, branchless possible but clarity here
        if next_head.wrapping_sub(tail) > RING_SIZE as u64 {
            return false; // ring full
        }
        
        unsafe {
            ptr::write(
                self.buffer.add((head & RING_MASK as u64) as usize),
                event,
            );
        }
        
        self.head.store(next_head, Ordering::Release);
        true
    }

    #[inline(always)]
    fn pop(&self) -> Option<CognitiveEvent> {
        let tail = self.tail.load(Ordering::Relaxed);
        let head = self.head.load(Ordering::Acquire);
        
        if tail == head {
            return None; // empty
        }
        
        let event = unsafe { ptr::read(self.buffer.add((tail & RING_MASK as u64) as usize)) };
        self.tail.store(tail.wrapping_add(1), Ordering::Release);
        Some(event)
    }
}

impl Drop for LockFreeRing {
    fn drop(&mut self) {
        let layout = Layout::array::<CognitiveEvent>(RING_SIZE).unwrap();
        unsafe { dealloc(self.buffer as *mut u8, layout) };
    }
}