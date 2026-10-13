#![allow(dead_code)]
use std::alloc::{alloc, dealloc, Layout};
use std::ptr;

const GRID_SHIFT: u32 = 8; // 256-unit cells
const CELL_MASK: u32 = 0xFF;
const BUCKET_SIZE: usize = 16; // cache line aligned
const MAX_ITEMS: usize = 4096;

#[repr(C, align(64))]
struct SpatialCell {
    items: [u32; BUCKET_SIZE], // indices, not pointers
    count: u8,
    _pad: [u8; 47], // force 64-byte alignment
}

#[repr(C, align(64))]
pub struct SpatialHash {
    cells: *mut SpatialCell,
    grid_size: u32,
    inv_cell_size: f32, // multiply instead of divide
}

impl SpatialHash {
    pub fn new(world_size: f32, cell_size: f32) -> Self {
        let grid_size = ((world_size / cell_size) as u32).next_power_of_two();
        let count = (grid_size * grid_size * grid_size) as usize;
        
        let layout = Layout::from_size_align(
            count * std::mem::size_of::<SpatialCell>(),
            64
        ).unwrap();
        
        let cells = unsafe {
            let ptr = alloc(layout) as *mut SpatialCell;
            ptr::write_bytes(ptr, 0, count);
            ptr
        };
        
        Self { cells, grid_size, inv_cell_size: 1.0 / cell_size }
    }
    
    #[inline(always)]
    fn hash(&self, x: f32, y: f32, z: f32) -> usize {
        // hot path: no branches, multiply-shift pattern
        let ix = ((x * self.inv_cell_size) as u32) & (self.grid_size - 1);
        let iy = ((y * self.inv_cell_size) as u32) & (self.grid_size - 1);
        let iz = ((z * self.inv_cell_size) as u32) & (self.grid_size - 1);
        
        ((ix * 73856093) ^ (iy * 19349663) ^ (iz * 83492791)) as usize % 
            (self.grid_size * self.grid_size * self.grid_size) as usize
    }
    
    #[inline(always)]
    pub fn insert(&mut self, x: f32, y: f32, z: f32, item_id: u32) -> bool {
        let idx = self.hash(x, y, z);
        unsafe {
            let cell = &mut *self.cells.add(idx);
            if (cell.count as usize) < BUCKET_SIZE {
                cell.items[cell.count as usize] = item_id;
                cell.count += 1;
                true
            } else {
                false // overflow, caller handles
            }
        }
    }
    
    #[inline(always)]
    pub fn query(&self, x: f32, y: f32, z: f32, out: &mut [u32; BUCKET_SIZE]) -> u8 {
        let idx = self.hash(x, y, z);
        unsafe {
            let cell = &*self.cells.add(idx);
            ptr::copy_nonoverlapping(cell.items.as_ptr(), out.as_mut_ptr(), BUCKET_SIZE);
            cell.count
        }
    }
}

impl Drop for SpatialHash {
    fn drop(&mut self) {
        let count = (self.grid_size * self.grid_size * self.grid_size) as usize;
        let layout = Layout::from_size_align(
            count * std::mem::size_of::<SpatialCell>(),
            64
        ).unwrap();
        unsafe { dealloc(self.cells as *mut u8, layout); }
    }
}