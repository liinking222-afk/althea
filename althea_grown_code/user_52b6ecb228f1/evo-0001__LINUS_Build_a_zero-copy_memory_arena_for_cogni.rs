use std::alloc::{alloc, dealloc, Layout};
use std::ptr::NonNull;
use std::marker::PhantomData;

const ARENA_SIZE: usize = 64 * 1024; // 64KB aligned page
const ALIGN: usize = 64; // Cache line alignment

pub struct CognitiveArena {
    base: NonNull<u8>,
    offset: usize,
    layout: Layout,
}

impl CognitiveArena {
    pub fn new() -> Self {
        let layout = Layout::from_size_align(ARENA_SIZE, ALIGN).unwrap();
        let base = unsafe { NonNull::new_unchecked(alloc(layout)) };
        Self { base, offset: 0, layout }
    }

    pub fn alloc<T>(&mut self) -> Option<&mut T> {
        let size = std::mem::size_of::<T>();
        let align = std::mem::align_of::<T>();
        let offset = (self.offset + align - 1) & !(align - 1);
        
        if offset + size > ARENA_SIZE { return None; }
        
        let ptr = unsafe { self.base.as_ptr().add(offset) as *mut T };
        self.offset = offset + size;
        unsafe { Some(&mut *ptr) }
    }

    pub fn alloc_slice<T>(&mut self, count: usize) -> Option<&mut [T]> {
        let size = std::mem::size_of::<T>() * count;
        let align = std::mem::align_of::<T>();
        let offset = (self.offset + align - 1) & !(align - 1);
        
        if offset + size > ARENA_SIZE { return None; }
        
        let ptr = unsafe { self.base.as_ptr().add(offset) as *mut T };
        self.offset = offset + size;
        unsafe { Some(std::slice::from_raw_parts_mut(ptr, count)) }
    }

    #[inline]
    pub fn reset(&mut self) {
        self.offset = 0;
    }

    #[inline]
    pub fn bytes_used(&self) -> usize { self.offset }

    #[inline]
    pub fn bytes_free(&self) -> usize { ARENA_SIZE - self.offset }
}

impl Drop for CognitiveArena {
    fn drop(&mut self) {
        unsafe { dealloc(self.base.as_ptr(), self.layout); }
    }
}

unsafe impl Send for CognitiveArena {}
unsafe impl Sync for CognitiveArena {}

#[repr(C, align(64))]
pub struct ModuleState<T> {
    data: T,
    _pad: PhantomData<u8>,
}

impl<T> ModuleState<T> {
    pub fn new(data: T) -> Self { Self { data, _pad: PhantomData } }
    pub fn get(&self) -> &T { &self.data }
    pub fn get_mut(&mut self) -> &mut T { &mut self.data }
}