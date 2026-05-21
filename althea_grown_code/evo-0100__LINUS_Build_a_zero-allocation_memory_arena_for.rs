use std::alloc::{alloc, dealloc, Layout};
use std::ptr::NonNull;
use std::marker::PhantomData;

const ARENA_SIZE: usize = 1024 * 1024; // 1MB slab

pub struct Arena {
    base: NonNull<u8>,
    offset: usize,
    capacity: usize,
    layout: Layout,
}

impl Arena {
    pub fn new() -> Self {
        let layout = Layout::from_size_align(ARENA_SIZE, 64).unwrap();
        let base = unsafe { NonNull::new_unchecked(alloc(layout)) };
        Arena { base, offset: 0, capacity: ARENA_SIZE, layout }
    }

    pub fn alloc<T>(&mut self) -> Option<NonNull<T>> {
        let align = std::mem::align_of::<T>();
        let size = std::mem::size_of::<T>();
        let padding = (align - (self.offset % align)) % align;
        let aligned_offset = self.offset + padding;
        
        if aligned_offset + size > self.capacity {
            return None;
        }
        
        let ptr = unsafe {
            NonNull::new_unchecked(self.base.as_ptr().add(aligned_offset) as *mut T)
        };
        self.offset = aligned_offset + size;
        Some(ptr)
    }

    pub fn reset(&mut self) {
        self.offset = 0;
    }

    pub fn usage(&self) -> f32 {
        (self.offset as f32) / (self.capacity as f32)
    }
}

impl Drop for Arena {
    fn drop(&mut self) {
        unsafe { dealloc(self.base.as_ptr(), self.layout); }
    }
}

pub struct ArenaVec<T> {
    ptr: NonNull<T>,
    len: usize,
    cap: usize,
    _marker: PhantomData<T>,
}

impl<T> ArenaVec<T> {
    pub fn new_in(arena: &mut Arena, capacity: usize) -> Option<Self> {
        let layout = Layout::array::<T>(capacity).ok()?;
        let align = layout.align();
        let size = layout.size();
        let padding = (align - (arena.offset % align)) % align;
        let aligned_offset = arena.offset + padding;
        
        if aligned_offset + size > arena.capacity {
            return None;
        }
        
        let ptr = unsafe {
            NonNull::new_unchecked(arena.base.as_ptr().add(aligned_offset) as *mut T)
        };
        arena.offset = aligned_offset + size;
        Some(ArenaVec { ptr, len: 0, cap: capacity, _marker: PhantomData })
    }

    pub fn push(&mut self, value: T) -> bool {
        if self.len >= self.cap { return false; }
        unsafe { self.ptr.as_ptr().add(self.len).write(value); }
        self.len += 1;
        true
    }
}