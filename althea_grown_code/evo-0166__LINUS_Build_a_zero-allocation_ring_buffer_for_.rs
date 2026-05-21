use std::mem::MaybeUninit;

const TRACE_CAPACITY: usize = 4096;

#[repr(C)]
pub struct TraceEvent {
    pub timestamp_ns: u64,
    pub event_type: u8,
    pub integrity_delta: i16,
    pub coherence_delta: i16,
    pub payload: [u8; 56],
}

pub struct TraceRing {
    buffer: [MaybeUninit<TraceEvent>; TRACE_CAPACITY],
    head: usize,
    count: usize,
}

impl TraceRing {
    pub const fn new() -> Self {
        Self {
            buffer: unsafe { MaybeUninit::uninit().assume_init() },
            head: 0,
            count: 0,
        }
    }

    #[inline(always)]
    pub fn push(&mut self, event: TraceEvent) {
        let idx = self.head;
        self.buffer[idx].write(event);
        self.head = (self.head + 1) & (TRACE_CAPACITY - 1);
        if self.count < TRACE_CAPACITY {
            self.count += 1;
        }
    }

    #[inline(always)]
    pub fn get_recent(&self, offset: usize) -> Option<&TraceEvent> {
        if offset >= self.count {
            return None;
        }
        let idx = (self.head + TRACE_CAPACITY - 1 - offset) & (TRACE_CAPACITY - 1);
        Some(unsafe { self.buffer[idx].assume_init_ref() })
    }

    #[inline(always)]
    pub fn scan_backward<F>(&self, mut predicate: F) -> Option<&TraceEvent>
    where
        F: FnMut(&TraceEvent) -> bool,
    {
        for offset in 0..self.count {
            let idx = (self.head + TRACE_CAPACITY - 1 - offset) & (TRACE_CAPACITY - 1);
            let event = unsafe { self.buffer[idx].assume_init_ref() };
            if predicate(event) {
                return Some(event);
            }
        }
        None
    }

    #[inline(always)]
    pub fn len(&self) -> usize {
        self.count
    }

    #[inline(always)]
    pub fn capacity(&self) -> usize {
        TRACE_CAPACITY
    }
}

static mut GLOBAL_TRACE: TraceRing = TraceRing::new();

pub fn record(event: TraceEvent) {
    unsafe { GLOBAL_TRACE.push(event) }
}

pub fn query_recent(offset: usize) -> Option<&'static TraceEvent> {
    unsafe { GLOBAL_TRACE.get_recent(offset) }
}