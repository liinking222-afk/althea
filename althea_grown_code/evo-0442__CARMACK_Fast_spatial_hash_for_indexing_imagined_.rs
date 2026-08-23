use std::mem::MaybeUninit;

const HASH_SIZE: usize = 1024; // Power of 2 for bitmasking
const PROBE_MAX: usize = 8; // Linear probe limit for cache locality

#[repr(C, align(32))] // Cache line aligned for prefetch
struct SpatialEntry {
    hash: u64,        // FNV-1a hash of xyz quantized coords
    id: u32,          // Diagram ID
    layer_depth: f32, // Z-depth for cross-sections
    _pad: u32,        // Align to 16 bytes
}

pub struct SpatialIndex {
    entries: Box<[SpatialEntry; HASH_SIZE]>,
    count: usize,
}

impl SpatialIndex {
    #[inline(always)]
    pub fn new() -> Self {
        let entries = unsafe {
            let mut arr: MaybeUninit<[SpatialEntry; HASH_SIZE]> = MaybeUninit::uninit();
            let ptr = arr.as_mut_ptr() as *mut SpatialEntry;
            for i in 0..HASH_SIZE {
                ptr.add(i).write(SpatialEntry { hash: 0, id: 0, layer_depth: 0.0, _pad: 0 });
            }
            Box::new(arr.assume_init())
        };
        Self { entries, count: 0 }
    }

    #[inline(always)]
    fn spatial_hash(x: f32, y: f32, z: f32) -> u64 {
        // Quantize to 0.1mm precision, FNV-1a for mixing
        let qx = (x * 10.0) as i32;
        let qy = (y * 10.0) as i32;
        let qz = (z * 10.0) as i32;
        
        let mut h: u64 = 0xcbf29ce484222325;
        h ^= qx as u64; h = h.wrapping_mul(0x100000001b3);
        h ^= qy as u64; h = h.wrapping_mul(0x100000001b3);
        h ^= qz as u64; h = h.wrapping_mul(0x100000001b3);
        h
    }

    #[inline]
    pub fn insert(&mut self, x: f32, y: f32, z: f32, id: u32, depth: f32) -> bool {
        if self.count >= HASH_SIZE * 3 / 4 { return false; } // Load factor guard
        
        let hash = Self::spatial_hash(x, y, z);
        let mut idx = (hash as usize) & (HASH_SIZE - 1);
        
        // Linear probe with early exit
        for _ in 0..PROBE_MAX {
            let entry = &mut self.entries[idx];
            if entry.hash == 0 {
                entry.hash = hash;
                entry.id = id;
                entry.layer_depth = depth;
                self.count += 1;
                return true;
            }
            idx = (idx + 1) & (HASH_SIZE - 1); // Sequential access for cache
        }
        false
    }

    #[inline]
    pub fn query(&self, x: f32, y: f32, z: f32) -> Option<(u32, f32)> {
        let hash = Self::spatial_hash(x, y, z);
        let mut idx = (hash as usize) & (HASH_SIZE - 1);
        
        for _ in 0..PROBE_MAX {
            let entry = &self.entries[idx];
            if entry.hash == hash { return Some((entry.id, entry.layer_depth)); }
            if entry.hash == 0 { return None; }
            idx = (idx + 1) & (HASH_SIZE - 1);
        }
        None
    }
}