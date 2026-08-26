use std::sync::atomic::{AtomicUsize, Ordering};
use std::mem::MaybeUninit;

const RING_SIZE: usize = 256;

#[repr(C)]
pub struct ArtifactEntry {
    pub timestamp_us: u64,
    pub artifact_type: u8,
    pub hash: u64,
    pub payload: [u8; 120],
}

pub struct ImagRingBuffer {
    entries: [MaybeUninit<ArtifactEntry>; RING_SIZE],
    head: AtomicUsize,
    tail: AtomicUsize,
}

impl ImagRingBuffer {
    pub const fn new() -> Self {
        Self {
            entries: unsafe { MaybeUninit::uninit().assume_init() },
            head: AtomicUsize::new(0),
            tail: AtomicUsize::new(0),
        }
    }

    #[inline]
    pub fn push(&mut self, entry: ArtifactEntry) -> bool {
        let head = self.head.load(Ordering::Relaxed);
        let tail = self.tail.load(Ordering::Acquire);
        let next = (head + 1) & (RING_SIZE - 1);
        
        if next == tail {
            self.tail.store((tail + 1) & (RING_SIZE - 1), Ordering::Release);
        }
        
        self.entries[head].write(entry);
        self.head.store(next, Ordering::Release);
        true
    }

    #[inline]
    pub fn read_latest(&self, out: &mut [ArtifactEntry], max: usize) -> usize {
        let head = self.head.load(Ordering::Acquire);
        let tail = self.tail.load(Ordering::Relaxed);
        let count = if head >= tail { head - tail } else { RING_SIZE - tail + head };
        let n = count.min(max).min(out.len());
        
        for i in 0..n {
            let idx = (head.wrapping_sub(i + 1)) & (RING_SIZE - 1);
            unsafe { out[i] = self.entries[idx].assume_init_ref().clone(); }
        }
        n
    }

    #[inline]
    pub fn evict_older_than(&mut self, threshold_us: u64) {
        let mut tail = self.tail.load(Ordering::Relaxed);
        let head = self.head.load(Ordering::Acquire);
        
        while tail != head {
            let entry = unsafe { self.entries[tail].assume_init_ref() };
            if entry.timestamp_us >= threshold_us { break; }
            tail = (tail + 1) & (RING_SIZE - 1);
        }
        
        self.tail.store(tail, Ordering::Release);
    }
}

impl Clone for ArtifactEntry {
    fn clone(&self) -> Self { unsafe { std::ptr::read(self) } }
}