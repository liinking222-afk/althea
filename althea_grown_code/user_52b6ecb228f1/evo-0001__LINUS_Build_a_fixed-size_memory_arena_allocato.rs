use std::alloc::{alloc, dealloc, Layout};
use std::ptr::NonNull;
use std::cell::Cell;

const ARENA_SIZE: usize = 1 << 20; // 1MB arena
const ALIGNMENT: usize = 8;

pub struct Arena {
    base: NonNull<u8>,
    offset: Cell<usize>,
    capacity: usize,
}

impl Arena {
    pub fn new() -> Self {
        let layout = Layout::from_size_align(ARENA_SIZE, ALIGNMENT).unwrap();
        let base = unsafe { NonNull::new_unchecked(alloc(layout)) };
        Arena {
            base,
            offset: Cell::new(0),
            capacity: ARENA_SIZE,
        }
    }

    #[inline(always)]
    pub fn alloc<T>(&self, value: T) -> *mut T {
        let size = std::mem::size_of::<T>();
        let align = std::mem::align_of::<T>();
        let current = self.offset.get();
        let aligned = (current + align - 1) & !(align - 1);
        let next = aligned + size;
        
        if next > self.capacity {
            panic!("arena exhausted");
        }
        
        self.offset.set(next);
        let ptr = unsafe { self.base.as_ptr().add(aligned) as *mut T };
        unsafe { ptr.write(value) };
        ptr
    }

    #[inline(always)]
    pub fn reset(&self) {
        self.offset.set(0);
    }

    pub fn used(&self) -> usize {
        self.offset.get()
    }
}

impl Drop for Arena {
    fn drop(&mut self) {
        let layout = Layout::from_size_align(ARENA_SIZE, ALIGNMENT).unwrap();
        unsafe { dealloc(self.base.as_ptr(), layout) };
    }
}

unsafe impl Send for Arena {}
unsafe impl Sync for Arena {}

#[repr(C, align(64))]
pub struct Event {
    pub timestamp_ns: u64,
    pub event_type: u32,
    pub payload: u64,
}