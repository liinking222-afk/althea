use std::alloc::{alloc, dealloc, Layout};
use std::ptr;

const FRAGMENT_SIZE: usize = 256;
const ARENA_CAPACITY: usize = 4096;

#[repr(C)]
struct Fragment {
    data: [u8; FRAGMENT_SIZE],
    next: *mut Fragment,
    hash: u64,
    flags: u8,
}

const FLAG_VALID: u8 = 0x01;
const FLAG_TRUNCATED: u8 = 0x02;
const FLAG_COALESCEABLE: u8 = 0x04;

pub struct ArenaAllocator {
    base: *mut Fragment,
    free_list: *mut Fragment,
    count: usize,
}

impl ArenaAllocator {
    pub fn new() -> Self {
        let layout = Layout::array::<Fragment>(ARENA_CAPACITY).unwrap();
        let base = unsafe { alloc(layout) as *mut Fragment };
        
        unsafe {
            for i in 0..ARENA_CAPACITY - 1 {
                let frag = base.add(i);
                (*frag).next = base.add(i + 1);
                (*frag).flags = 0;
            }
            (*base.add(ARENA_CAPACITY - 1)).next = ptr::null_mut();
        }
        
        ArenaAllocator { base, free_list: base, count: 0 }
    }
    
    pub fn alloc_fragment(&mut self, data: &[u8]) -> *mut Fragment {
        if self.free_list.is_null() { return ptr::null_mut(); }
        
        unsafe {
            let frag = self.free_list;
            self.free_list = (*frag).next;
            
            let len = data.len().min(FRAGMENT_SIZE);
            ptr::copy_nonoverlapping(data.as_ptr(), (*frag).data.as_mut_ptr(), len);
            (*frag).hash = self.hash_data(&(*frag).data[..len]);
            (*frag).flags = if len < data.len() { FLAG_TRUNCATED } else { FLAG_VALID };
            (*frag).next = ptr::null_mut();
            
            self.count += 1;
            frag
        }
    }
    
    pub fn scan_integrity(&self) -> (usize, usize) {
        let mut valid = 0;
        let mut truncated = 0;
        
        unsafe {
            for i in 0..self.count {
                let frag = self.base.add(i);
                if (*frag).flags & FLAG_VALID != 0 { valid += 1; }
                if (*frag).flags & FLAG_TRUNCATED != 0 { truncated += 1; }
            }
        }
        (valid, truncated)
    }
    
    fn hash_data(&self, data: &[u8]) -> u64 {
        data.iter().fold(0xcbf29ce484222325u64, |h, &b| 
            (h ^ b as u64).wrapping_mul(0x100000001b3))
    }
}

impl Drop for ArenaAllocator {
    fn drop(&mut self) {
        unsafe {
            let layout = Layout::array::<Fragment>(ARENA_CAPACITY).unwrap();
            dealloc(self.base as *mut u8, layout);
        }
    }
}