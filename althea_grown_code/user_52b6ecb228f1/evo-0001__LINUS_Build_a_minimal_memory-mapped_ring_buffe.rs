use std::sync::atomic::{AtomicUsize, Ordering};
use std::alloc::{alloc, dealloc, Layout};
use std::ptr;

const RING_SIZE: usize = 4096; // power of 2
const MASK: usize = RING_SIZE - 1;

#[repr(C)]
struct CognitiveEvent {
    timestamp_ns: u64,
    module_id: u32,
    event_type: u16,
    coherence_delta: i16,
}

pub struct CognitiveRingBuffer {
    buffer: *mut CognitiveEvent,
    head: AtomicUsize,
    tail: AtomicUsize,
    layout: Layout,
}

impl CognitiveRingBuffer {
    pub fn new() -> Self {
        let layout = Layout::array::<CognitiveEvent>(RING_SIZE).unwrap();
        let buffer = unsafe { alloc(layout) as *mut CognitiveEvent };
        Self {
            buffer,
            head: AtomicUsize::new(0),
            tail: AtomicUsize::new(0),
            layout,
        }
    }

    #[inline(always)]
    pub fn push(&self, event: CognitiveEvent) -> bool {
        let tail = self.tail.load(Ordering::Relaxed);
        let next_tail = (tail + 1) & MASK;
        let head = self.head.load(Ordering::Acquire);
        
        if next_tail == head { return false; }
        
        unsafe { ptr::write(self.buffer.add(tail), event); }
        self.tail.store(next_tail, Ordering::Release);
        true
    }

    #[inline(always)]
    pub fn pop(&self) -> Option<CognitiveEvent> {
        let head = self.head.load(Ordering::Relaxed);
        let tail = self.tail.load(Ordering::Acquire);
        
        if head == tail { return None; }
        
        let event = unsafe { ptr::read(self.buffer.add(head)) };
        let next_head = (head + 1) & MASK;
        self.head.store(next_head, Ordering::Release);
        Some(event)
    }

    #[inline(always)]
    pub fn peek(&self, offset: usize) -> Option<&CognitiveEvent> {
        let head = self.head.load(Ordering::Acquire);
        let tail = self.tail.load(Ordering::Acquire);
        let len = (tail.wrapping_sub(head)) & MASK;
        
        if offset >= len { return None; }
        unsafe { Some(&*self.buffer.add((head + offset) & MASK)) }
    }
}

impl Drop for CognitiveRingBuffer {
    fn drop(&mut self) {
        unsafe { dealloc(self.buffer as *mut u8, self.layout); }
    }
}

unsafe impl Send for CognitiveRingBuffer {}
unsafe impl Sync for CognitiveRingBuffer {}