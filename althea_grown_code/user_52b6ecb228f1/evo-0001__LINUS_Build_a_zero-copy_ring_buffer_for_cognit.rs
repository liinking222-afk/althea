use std::sync::atomic::{AtomicUsize, Ordering};
use std::alloc::{alloc, dealloc, Layout};
use std::ptr;

const EVENT_SIZE: usize = 64;  // Fixed-width event records
const BUFFER_CAPACITY: usize = 4096;  // Power of 2 for mask optimization

#[repr(C, align(64))]
struct Event {
    timestamp_us: u64,
    event_type: u32,
    module_id: u32,
    payload: [u8; 48],
}

pub struct EventRingBuffer {
    buffer: *mut Event,
    capacity: usize,
    write_pos: AtomicUsize,
    read_pos: AtomicUsize,
    layout: Layout,
}

impl EventRingBuffer {
    pub fn new() -> Self {
        let layout = Layout::from_size_align(
            EVENT_SIZE * BUFFER_CAPACITY,
            64
        ).unwrap();
        
        let buffer = unsafe { alloc(layout) as *mut Event };
        
        Self {
            buffer,
            capacity: BUFFER_CAPACITY,
            write_pos: AtomicUsize::new(0),
            read_pos: AtomicUsize::new(0),
            layout,
        }
    }
    
    pub fn write(&self, event_type: u32, module_id: u32, payload: &[u8; 48]) -> bool {
        let write_idx = self.write_pos.load(Ordering::Relaxed);
        let read_idx = self.read_pos.load(Ordering::Acquire);
        
        if ((write_idx + 1) & (self.capacity - 1)) == read_idx {
            return false;  // Buffer full
        }
        
        let slot = unsafe { self.buffer.add(write_idx & (self.capacity - 1)) };
        
        unsafe {
            ptr::write(slot, Event {
                timestamp_us: std::time::SystemTime::now()
                    .duration_since(std::time::UNIX_EPOCH)
                    .unwrap()
                    .as_micros() as u64,
                event_type,
                module_id,
                payload: *payload,
            });
        }
        
        self.write_pos.store(write_idx + 1, Ordering::Release);
        true
    }
    
    pub fn read(&self) -> Option<&Event> {
        let read_idx = self.read_pos.load(Ordering::Relaxed);
        let write_idx = self.write_pos.load(Ordering::Acquire);
        
        if read_idx == write_idx {
            return None;
        }
        
        let slot = unsafe { &*self.buffer.add(read_idx & (self.capacity - 1)) };
        self.read_pos.store(read_idx + 1, Ordering::Release);
        Some(slot)
    }
}

impl Drop for EventRingBuffer {
    fn drop(&mut self) {
        unsafe { dealloc(self.buffer as *mut u8, self.layout); }
    }
}

unsafe impl Send for EventRingBuffer {}
unsafe impl Sync for EventRingBuffer {}