use std::sync::atomic::{AtomicUsize, Ordering};
use std::cell::UnsafeCell;

const SLOT_SIZE: usize = 256;
const SLOT_COUNT: usize = 1024;
const BUFFER_SIZE: usize = SLOT_SIZE * SLOT_COUNT;

#[repr(C, align(64))]
struct Slot {
    len: u8,
    data: [u8; SLOT_SIZE - 1],
}

pub struct RingBuffer {
    buffer: UnsafeCell<[Slot; SLOT_COUNT]>,
    write_idx: AtomicUsize,
    read_idx: AtomicUsize,
}

unsafe impl Sync for RingBuffer {}

impl RingBuffer {
    pub const fn new() -> Self {
        const EMPTY_SLOT: Slot = Slot { len: 0, data: [0; SLOT_SIZE - 1] };
        Self {
            buffer: UnsafeCell::new([EMPTY_SLOT; SLOT_COUNT]),
            write_idx: AtomicUsize::new(0),
            read_idx: AtomicUsize::new(0),
        }
    }

    pub fn push(&self, data: &[u8]) -> bool {
        if data.len() >= SLOT_SIZE { return false; }
        
        let widx = self.write_idx.load(Ordering::Relaxed);
        let ridx = self.read_idx.load(Ordering::Acquire);
        
        if (widx + 1) % SLOT_COUNT == ridx % SLOT_COUNT { return false; }
        
        unsafe {
            let slot = &mut (*self.buffer.get())[widx % SLOT_COUNT];
            slot.len = data.len() as u8;
            slot.data[..data.len()].copy_from_slice(data);
        }
        
        self.write_idx.store(widx + 1, Ordering::Release);
        true
    }

    pub fn pop(&self, out: &mut [u8]) -> Option<usize> {
        let ridx = self.read_idx.load(Ordering::Relaxed);
        let widx = self.write_idx.load(Ordering::Acquire);
        
        if ridx == widx { return None; }
        
        unsafe {
            let slot = &(*self.buffer.get())[ridx % SLOT_COUNT];
            let len = slot.len as usize;
            if out.len() < len { return None; }
            out[..len].copy_from_slice(&slot.data[..len]);
            self.read_idx.store(ridx + 1, Ordering::Release);
            Some(len)
        }
    }

    pub fn available(&self) -> usize {
        let w = self.write_idx.load(Ordering::Relaxed);
        let r = self.read_idx.load(Ordering::Relaxed);
        (w - r) % SLOT_COUNT
    }
}