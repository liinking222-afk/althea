use std::sync::atomic::{AtomicU64, Ordering};
use std::alloc::{alloc, dealloc, Layout};
use std::ptr;

const CACHELINE: usize = 64;
const SLOT_SIZE: usize = 256;
const SLOT_COUNT: usize = 1024;

#[repr(C, align(64))]
struct Slot {
    seq: AtomicU64,
    data: [u8; SLOT_SIZE - 8],
}

pub struct RingBuffer {
    buffer: *mut Slot,
    layout: Layout,
    write_pos: AtomicU64,
    read_pos: AtomicU64,
}

impl RingBuffer {
    pub fn new() -> Self {
        let layout = Layout::from_size_align(
            SLOT_COUNT * SLOT_SIZE,
            CACHELINE
        ).unwrap();
        
        let buffer = unsafe { alloc(layout) as *mut Slot };
        
        for i in 0..SLOT_COUNT {
            unsafe {
                ptr::write(
                    buffer.add(i),
                    Slot {
                        seq: AtomicU64::new(0),
                        data: [0u8; SLOT_SIZE - 8],
                    }
                );
            }
        }
        
        RingBuffer {
            buffer,
            layout,
            write_pos: AtomicU64::new(0),
            read_pos: AtomicU64::new(0),
        }
    }
    
    pub fn write(&self, data: &[u8]) -> bool {
        if data.len() > SLOT_SIZE - 8 { return false; }
        
        let pos = self.write_pos.fetch_add(1, Ordering::Relaxed);
        let slot = unsafe { &*self.buffer.add((pos % SLOT_COUNT as u64) as usize) };
        
        unsafe {
            ptr::copy_nonoverlapping(
                data.as_ptr(),
                slot.data.as_ptr() as *mut u8,
                data.len()
            );
        }
        
        slot.seq.store(pos + 1, Ordering::Release);
        true
    }
    
    pub fn read(&self, buf: &mut [u8]) -> Option<usize> {
        let pos = self.read_pos.load(Ordering::Relaxed);
        let slot = unsafe { &*self.buffer.add((pos % SLOT_COUNT as u64) as usize) };
        
        let seq = slot.seq.load(Ordering::Acquire);
        if seq <= pos { return None; }
        
        let len = buf.len().min(SLOT_SIZE - 8);
        unsafe {
            ptr::copy_nonoverlapping(
                slot.data.as_ptr(),
                buf.as_mut_ptr(),
                len
            );
        }
        
        self.read_pos.store(pos + 1, Ordering::Release);
        Some(len)
    }
}

impl Drop for RingBuffer {
    fn drop(&mut self) {
        unsafe { dealloc(self.buffer as *mut u8, self.layout); }
    }
}

unsafe impl Send for RingBuffer {}
unsafe impl Sync for RingBuffer {}