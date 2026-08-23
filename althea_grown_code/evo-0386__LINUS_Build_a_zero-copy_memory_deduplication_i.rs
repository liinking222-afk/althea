use std::collections::HashMap;
use std::hash::{Hash, Hasher};
use std::collections::hash_map::DefaultHasher;

const CHUNK_SIZE: usize = 64;
const SIMILARITY_THRESHOLD: f32 = 0.42;

#[repr(C)]
struct MemoryBlock {
    id: u64,
    data: Vec<u8>,
    fingerprint: u64,
    chunk_hashes: Vec<u64>,
}

struct DeduplicationIndex {
    fingerprints: HashMap<u64, Vec<u64>>,
    chunk_index: HashMap<u64, Vec<(u64, usize)>>,
    blocks: HashMap<u64, MemoryBlock>,
}

impl DeduplicationIndex {
    fn new() -> Self {
        DeduplicationIndex {
            fingerprints: HashMap::with_capacity(4096),
            chunk_index: HashMap::with_capacity(16384),
            blocks: HashMap::with_capacity(4096),
        }
    }

    fn hash_bytes(&self, data: &[u8]) -> u64 {
        let mut hasher = DefaultHasher::new();
        data.hash(&mut hasher);
        hasher.finish()
    }

    fn insert(&mut self, id: u64, data: Vec<u8>) -> Vec<u64> {
        let fingerprint = self.hash_bytes(&data);
        let mut chunk_hashes = Vec::with_capacity(data.len() / CHUNK_SIZE + 1);
        
        for (idx, chunk) in data.chunks(CHUNK_SIZE).enumerate() {
            let chunk_hash = self.hash_bytes(chunk);
            chunk_hashes.push(chunk_hash);
            self.chunk_index.entry(chunk_hash).or_insert_with(Vec::new).push((id, idx));
        }

        let block = MemoryBlock { id, data, fingerprint, chunk_hashes };
        self.blocks.insert(id, block);
        self.fingerprints.entry(fingerprint).or_insert_with(Vec::new).push(id);
        
        self.find_similar(id)
    }

    fn find_similar(&self, id: u64) -> Vec<u64> {
        let block = match self.blocks.get(&id) { Some(b) => b, None => return vec![] };
        let mut candidates: HashMap<u64, usize> = HashMap::new();

        for chunk_hash in &block.chunk_hashes {
            if let Some(refs) = self.chunk_index.get(chunk_hash) {
                for &(other_id, _) in refs {
                    if other_id != id {
                        *candidates.entry(other_id).or_insert(0) += 1;
                    }
                }
            }
        }

        let min_chunks = block.chunk_hashes.len();
        candidates.into_iter()
            .filter_map(|(other_id, shared)| {
                let similarity = shared as f32 / min_chunks as f32;
                if similarity >= SIMILARITY_THRESHOLD { Some(other_id) } else { None }
            })
            .collect()
    }

    fn deduplicate(&self) -> Vec<(u64, u64)> {
        self.fingerprints.iter()
            .filter(|(_, ids)| ids.len() > 1)
            .flat_map(|(_, ids)| {
                ids.windows(2).map(|w| (w[0], w[1])).collect::<Vec<_>>()
            })
            .collect()
    }
}