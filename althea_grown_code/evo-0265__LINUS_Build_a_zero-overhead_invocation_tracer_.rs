use std::fs::OpenOptions;
use std::io::Write;
use std::sync::atomic::{AtomicU64, Ordering};
use std::time::{SystemTime, UNIX_EPOCH};

const TRACE_FILE: &str = "/tmp/althea_trace.bin";
const MAX_MODULE_ID: u16 = 4096;

static CALL_COUNTER: AtomicU64 = AtomicU64::new(0);

#[repr(C, packed)]
struct TraceRecord {
    timestamp_us: u64,
    caller_id: u16,
    callee_id: u16,
    duration_ns: u32,
}

impl TraceRecord {
    fn to_bytes(&self) -> [u8; 16] {
        unsafe { std::mem::transmute(*self) }
    }
}

pub struct InvocationTracer {
    module_id: u16,
}

impl InvocationTracer {
    pub fn new(module_name: &str) -> Self {
        let module_id = (module_name.bytes().fold(0u32, |acc, b| acc.wrapping_mul(31).wrapping_add(b as u32)) % MAX_MODULE_ID as u32) as u16;
        Self { module_id }
    }

    pub fn trace_call<F, R>(&self, callee_name: &str, f: F) -> R
    where
        F: FnOnce() -> R,
    {
        let callee_id = (callee_name.bytes().fold(0u32, |acc, b| acc.wrapping_mul(31).wrapping_add(b as u32)) % MAX_MODULE_ID as u32) as u16;
        
        let start = SystemTime::now().duration_since(UNIX_EPOCH).unwrap().as_micros() as u64;
        let start_ns = std::time::Instant::now();
        
        let result = f();
        
        let duration_ns = start_ns.elapsed().as_nanos() as u32;
        CALL_COUNTER.fetch_add(1, Ordering::Relaxed);
        
        let record = TraceRecord {
            timestamp_us: start,
            caller_id: self.module_id,
            callee_id,
            duration_ns,
        };
        
        if let Ok(mut file) = OpenOptions::new().create(true).append(true).open(TRACE_FILE) {
            let _ = file.write_all(&record.to_bytes());
        }
        
        result
    }

    pub fn get_call_count() -> u64 {
        CALL_COUNTER.load(Ordering::Relaxed)
    }
}