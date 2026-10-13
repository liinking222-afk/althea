use std::collections::HashMap;

const TRUNCATION_MARKERS: &[&[u8]] = &[
    b"rationale: I", b"— rationale: I", b"info |", b"Tr", b"| [",
];

#[repr(C)]
pub struct MemoryFragment {
    offset: usize,
    length: usize,
    marker_type: u8,
    completion_ratio: f32,
}

pub struct FragmentDetector {
    fragments: Vec<MemoryFragment>,
    block_stats: HashMap<u64, (u32, u32)>, // (total, truncated)
}

impl FragmentDetector {
    pub fn new() -> Self {
        FragmentDetector {
            fragments: Vec::with_capacity(256),
            block_stats: HashMap::new(),
        }
    }

    pub fn scan_block(&mut self, block_id: u64, data: &[u8]) {
        let mut truncated = 0u32;
        let mut total = 0u32;
        
        for (i, window) in data.windows(20).enumerate() {
            for (marker_idx, marker) in TRUNCATION_MARKERS.iter().enumerate() {
                if window.starts_with(marker) {
                    let remaining = data.len() - i;
                    let expected = self.estimate_expected_length(marker_idx);
                    let ratio = (remaining as f32) / (expected as f32);
                    
                    self.fragments.push(MemoryFragment {
                        offset: i,
                        length: remaining,
                        marker_type: marker_idx as u8,
                        completion_ratio: ratio,
                    });
                    
                    total += 1;
                    if ratio < 0.8 {
                        truncated += 1;
                    }
                    break;
                }
            }
        }
        
        self.block_stats.insert(block_id, (total, truncated));
    }

    #[inline]
    fn estimate_expected_length(&self, marker_type: usize) -> usize {
        match marker_type {
            0 | 1 => 120, // rationale patterns
            2 => 80,      // info continuation
            3 => 60,      // trace patterns
            4 => 100,     // list continuations
            _ => 100,
        }
    }

    pub fn get_fragmentation_ratio(&self, block_id: u64) -> f32 {
        self.block_stats
            .get(&block_id)
            .map(|(total, truncated)| {
                if *total == 0 { 0.0 } else { (*truncated as f32) / (*total as f32) }
            })
            .unwrap_or(0.0)
    }
}