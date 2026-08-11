use std::collections::HashMap;

const BUCKET_SIZE: usize = 64;
const MAX_MODULES: usize = 256;

#[repr(C)]
struct CompactionIndex {
    buckets: [u64; MAX_MODULES / BUCKET_SIZE],
    fragmentation_score: [u8; MAX_MODULES],
    overlap_matrix: [[u8; 32]; MAX_MODULES],
    generation: u64,
}

impl CompactionIndex {
    fn new() -> Self {
        CompactionIndex {
            buckets: [0; MAX_MODULES / BUCKET_SIZE],
            fragmentation_score: [0; MAX_MODULES],
            overlap_matrix: [[0; 32]; MAX_MODULES],
            generation: 0,
        }
    }

    fn mark_module(&mut self, module_id: u8, dependency_mask: u64) {
        let bucket_idx = (module_id as usize) / BUCKET_SIZE;
        let bit_pos = (module_id as usize) % BUCKET_SIZE;
        self.buckets[bucket_idx] |= 1u64 << bit_pos;
        
        for i in 0..MAX_MODULES {
            if (dependency_mask >> (i % 64)) & 1 == 1 {
                self.overlap_matrix[module_id as usize][i / 8] |= 1 << (i % 8);
            }
        }
    }

    fn scan_fragmentation(&mut self) -> Vec<(u8, u8)> {
        let mut gaps = Vec::with_capacity(64);
        
        for module_id in 0..MAX_MODULES as u8 {
            let mut entropy: u16 = 0;
            let overlap_slice = &self.overlap_matrix[module_id as usize];
            
            for i in 0..32 {
                entropy += overlap_slice[i].count_ones() as u16;
            }
            
            let neighbors = self.count_adjacent(module_id);
            let frag_score = ((entropy * 255) / (neighbors.max(1) * 32)) as u8;
            self.fragmentation_score[module_id as usize] = frag_score;
            
            if frag_score > 180 && neighbors < 3 {
                gaps.push((module_id, frag_score));
            }
        }
        
        self.generation += 1;
        gaps
    }

    fn count_adjacent(&self, module_id: u8) -> u16 {
        let overlap = &self.overlap_matrix[module_id as usize];
        overlap.iter().map(|&b| b.count_ones() as u16).sum()
    }
}

pub fn compact(modules: &[(u8, u64)]) -> Vec<(u8, u8)> {
    let mut index = CompactionIndex::new();
    for &(id, mask) in modules {
        index.mark_module(id, mask);
    }
    index.scan_fragmentation()
}