use std::alloc::{alloc, dealloc, Layout};
use std::ptr::NonNull;
use std::cell::Cell;

pub struct Arena {
    chunk: NonNull<u8>,
    capacity: usize,
    offset: Cell<usize>,
}

impl Arena {
    pub fn new(capacity: usize) -> Self {
        let layout = Layout::from_size_align(capacity, 8).unwrap();
        let chunk = unsafe { NonNull::new_unchecked(alloc(layout)) };
        Arena { chunk, capacity, offset: Cell::new(0) }
    }

    pub fn alloc<T>(&self, value: T) -> &mut T {
        let size = std::mem::size_of::<T>();
        let align = std::mem::align_of::<T>();
        let offset = self.offset.get();
        let aligned = (offset + align - 1) & !(align - 1);
        
        assert!(aligned + size <= self.capacity, "arena exhausted");
        
        let ptr = unsafe { self.chunk.as_ptr().add(aligned) as *mut T };
        unsafe { ptr.write(value); }
        self.offset.set(aligned + size);
        unsafe { &mut *ptr }
    }

    pub fn alloc_slice<T: Copy>(&self, slice: &[T]) -> &mut [T] {
        let size = std::mem::size_of::<T>() * slice.len();
        let align = std::mem::align_of::<T>();
        let offset = self.offset.get();
        let aligned = (offset + align - 1) & !(align - 1);
        
        assert!(aligned + size <= self.capacity, "arena exhausted");
        
        let ptr = unsafe { self.chunk.as_ptr().add(aligned) as *mut T };
        unsafe { std::ptr::copy_nonoverlapping(slice.as_ptr(), ptr, slice.len()); }
        self.offset.set(aligned + size);
        unsafe { std::slice::from_raw_parts_mut(ptr, slice.len()) }
    }

    pub fn reset(&self) {
        self.offset.set(0);
    }

    pub fn used(&self) -> usize {
        self.offset.get()
    }
}

impl Drop for Arena {
    fn drop(&mut self) {
        let layout = Layout::from_size_align(self.capacity, 8).unwrap();
        unsafe { dealloc(self.chunk.as_ptr(), layout); }
    }
}

unsafe impl Send for Arena {}
unsafe impl Sync for Arena {}