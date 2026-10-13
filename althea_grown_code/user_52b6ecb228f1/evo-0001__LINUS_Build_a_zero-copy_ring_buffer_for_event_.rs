use std::sync::atomic::{AtomicUsize, Ordering};
use std::alloc::{alloc, dealloc, Layout};

const ENTRY_SIZE: usize = 64; // Cache line aligned
const RING_CAPACITY: usize = 4096;

#[repr(C, align(64))]
struct MetricEntry {
    timestamp_ns: u64,
    metric_type: u8,
    value: i32,
    padding: [u8; 51],
}

pub struct MetricRing {
    buffer: *mut MetricEntry,
    layout: Layout,
    write_pos: AtomicUsize,
    read_pos: AtomicUsize,
}

impl MetricRing {
    pub fn new() -> Self {
        let layout = Layout::from_size_align(
            ENTRY_SIZE * RING_CAPACITY,
            64
        ).unwrap();
        let buffer = unsafe { alloc(layout) as *mut MetricEntry };
        
        MetricRing {
            buffer,
            layout,
            write_pos: AtomicUsize::new(0),
            read_pos: AtomicUsize::new(0),
        }
    }

    #[inline(always)]
    pub fn write(&self, metric_type: u8, value: i32) -> bool {
        let write = self.write_pos.load(Ordering::Relaxed);
        let read = self.read_pos.load(Ordering::Acquire);
        
        if write - read >= RING_CAPACITY {
            return false;
        }
        
        unsafe {
            let entry = self.buffer.add(write & (RING_CAPACITY - 1));
            (*entry).timestamp_ns = std::time::SystemTime::now()
                .duration_since(std::time::UNIX_EPOCH)
                .unwrap()
                .as_nanos() as u64;
            (*entry).metric_type = metric_type;
            (*entry).value = value;
        }
        
        self.write_pos.store(write + 1, Ordering::Release);
        true
    }

    #[inline(always)]
    pub fn read(&self) -> Option<(u64, u8, i32)> {
        let read = self.read_pos.load(Ordering::Relaxed);
        let write = self.write_pos.load(Ordering::Acquire);
        
        if read >= write {
            return None;
        }
        
        let result = unsafe {
            let entry = self.buffer.add(read & (RING_CAPACITY - 1));
            ((*entry).timestamp_ns, (*entry).metric_type, (*entry).value)
        };
        
        self.read_pos.store(read + 1, Ordering::Release);
        Some(result)
    }
}

impl Drop for MetricRing {
    fn drop(&mut self) {
        unsafe { dealloc(self.buffer as *mut u8, self.layout) }
    }
}

unsafe impl Send for MetricRing {}
unsafe impl Sync for MetricRing {}