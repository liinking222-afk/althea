use std::alloc::{alloc, dealloc, Layout};
use std::ptr;

#[repr(C)]
struct MemBlock {
    addr: *mut u8,
    size: usize,
    semantic_hash: u64,
    ref_count: u32,
}

struct MemoryConsolidator {
    blocks: Vec<MemBlock>,
    arena_base: *mut u8,
    arena_size: usize,
}

impl MemoryConsolidator {
    unsafe fn new(arena_size: usize) -> Self {
        let layout = Layout::from_size_align_unchecked(arena_size, 8);
        let arena_base = alloc(layout);
        Self { blocks: Vec::with_capacity(256), arena_base, arena_size }
    }

    unsafe fn defrag_adjacent(&mut self) -> usize {
        self.blocks.sort_unstable_by_key(|b| b.addr as usize);
        let mut merged = 0;
        let mut i = 0;
        
        while i < self.blocks.len().saturating_sub(1) {
            let curr = &self.blocks[i];
            let next = &self.blocks[i + 1];
            let curr_end = curr.addr.add(curr.size);
            let hash_dist = curr.semantic_hash.abs_diff(next.semantic_hash);
            
            if curr_end == next.addr && hash_dist < 0x1000 {
                let new_size = curr.size + next.size;
                let new_hash = curr.semantic_hash.wrapping_add(next.semantic_hash) >> 1;
                ptr::copy_nonoverlapping(next.addr, curr_end, next.size);
                self.blocks[i].size = new_size;
                self.blocks[i].semantic_hash = new_hash;
                self.blocks.remove(i + 1);
                merged += 1;
            } else {
                i += 1;
            }
        }
        merged
    }

    unsafe fn compact_dead(&mut self) -> usize {
        let initial = self.blocks.len();
        self.blocks.retain(|b| b.ref_count > 0);
        let mut write_offset = 0usize;
        
        for block in &mut self.blocks {
            let src = block.addr;
            let dst = self.arena_base.add(write_offset);
            if src != dst {
                ptr::copy(src, dst, block.size);
                block.addr = dst;
            }
            write_offset += block.size;
        }
        initial - self.blocks.len()
    }
}

impl Drop for MemoryConsolidator {
    fn drop(&mut self) {
        unsafe {
            let layout = Layout::from_size_align_unchecked(self.arena_size, 8);
            dealloc(self.arena_base, layout);
        }
    }
}