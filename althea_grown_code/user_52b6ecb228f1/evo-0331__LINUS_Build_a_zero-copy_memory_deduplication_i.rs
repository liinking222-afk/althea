use std::collections::HashMap;
use std::hash::{Hash, Hasher};
use std::collections::hash_map::DefaultHasher;

const SHINGLE_SIZE: usize = 5;
const SIMILARITY_THRESHOLD: f32 = 0.7;

#[repr(C)]
struct MemoryEntry {
    id: u64,
    hash: u64,
    shingles: Vec<u64>,
}

struct DeduplicationIndex {
    entries: Vec<MemoryEntry>,
    shingle_map: HashMap<u64, Vec<usize>>,
}

impl DeduplicationIndex {
    fn new() -> Self {
        Self {
            entries: Vec::with_capacity(4096),
            shingle_map: HashMap::with_capacity(16384),
        }
    }

    fn hash_bytes(data: &[u8]) -> u64 {
        let mut hasher = DefaultHasher::new();
        data.hash(&mut hasher);
        hasher.finish()
    }

    fn extract_shingles(content: &str) -> Vec<u64> {
        let tokens: Vec<&str> = content.split_whitespace().collect();
        if tokens.len() < SHINGLE_SIZE {
            return vec![Self::hash_bytes(content.as_bytes())];
        }
        
        tokens.windows(SHINGLE_SIZE)
            .map(|window| Self::hash_bytes(window.join(" ").as_bytes()))
            .collect()
    }

    fn add_entry(&mut self, id: u64, content: &str) {
        let hash = Self::hash_bytes(content.as_bytes());
        let shingles = Self::extract_shingles(content);
        
        let entry_idx = self.entries.len();
        for &shingle in &shingles {
            self.shingle_map.entry(shingle).or_insert_with(Vec::new).push(entry_idx);
        }
        
        self.entries.push(MemoryEntry { id, hash, shingles });
    }

    fn find_duplicates(&self, idx: usize) -> Vec<(usize, f32)> {
        let entry = &self.entries[idx];
        let mut candidates: HashMap<usize, usize> = HashMap::new();
        
        for &shingle in &entry.shingles {
            if let Some(matches) = self.shingle_map.get(&shingle) {
                for &match_idx in matches {
                    if match_idx != idx {
                        *candidates.entry(match_idx).or_insert(0) += 1;
                    }
                }
            }
        }
        
        candidates.into_iter()
            .filter_map(|(other_idx, overlap)| {
                let similarity = overlap as f32 / entry.shingles.len().max(self.entries[other_idx].shingles.len()) as f32;
                if similarity >= SIMILARITY_THRESHOLD {
                    Some((other_idx, similarity))
                } else {
                    None
                }
            })
            .collect()
    }
}