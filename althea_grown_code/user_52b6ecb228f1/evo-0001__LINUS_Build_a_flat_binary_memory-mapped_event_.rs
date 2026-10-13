use std::alloc::{alloc, dealloc, Layout};
use std::ptr;
use std::sync::atomic::{AtomicU64, Ordering};

const EVENT_SIZE: usize = 128;
const MAX_EVENTS: usize = 65536;
const RING_MASK: u64 = (MAX_EVENTS - 1) as u64;

#[repr(C, align(64))]
struct EventRecord {
    timestamp_ns: u64,
    module_id: u32,
    event_type: u16,
    flags: u16,
    data: [u8; 112],
}

pub struct FlatEventLog {
    buffer: *mut EventRecord,
    write_head: AtomicU64,
    layout: Layout,
}

impl FlatEventLog {
    pub fn new() -> Self {
        let layout = Layout::from_size_align(
            EVENT_SIZE * MAX_EVENTS,
            64
        ).unwrap();
        
        let buffer = unsafe { alloc(layout) as *mut EventRecord };
        
        unsafe {
            ptr::write_bytes(buffer, 0, MAX_EVENTS);
        }
        
        Self {
            buffer,
            write_head: AtomicU64::new(0),
            layout,
        }
    }
    
    #[inline(always)]
    pub fn write(&self, module_id: u32, event_type: u16, data: &[u8]) -> u64 {
        let idx = self.write_head.fetch_add(1, Ordering::Relaxed);
        let slot = unsafe { self.buffer.add((idx & RING_MASK) as usize) };
        
        unsafe {
            (*slot).timestamp_ns = self.rdtsc();
            (*slot).module_id = module_id;
            (*slot).event_type = event_type;
            (*slot).flags = 0;
            ptr::copy_nonoverlapping(
                data.as_ptr(),
                (*slot).data.as_mut_ptr(),
                data.len().min(112)
            );
        }
        
        idx
    }
    
    #[inline(always)]
    pub fn read(&self, idx: u64) -> Option<EventRecord> {
        let current = self.write_head.load(Ordering::Relaxed);
        if idx >= current || current - idx > MAX_EVENTS as u64 {
            return None;
        }
        
        let slot = unsafe { self.buffer.add((idx & RING_MASK) as usize) };
        Some(unsafe { ptr::read(slot) })
    }
    
    #[cfg(target_arch = "x86_64")]
    #[inline(always)]
    fn rdtsc(&self) -> u64 {
        unsafe { core::arch::x86_64::_rdtsc() }
    }
}

impl Drop for FlatEventLog {
    fn drop(&mut self) {
        unsafe { dealloc(self.buffer as *mut u8, self.layout); }
    }
}

unsafe impl Send for FlatEventLog {}
unsafe impl Sync for FlatEventLog {}