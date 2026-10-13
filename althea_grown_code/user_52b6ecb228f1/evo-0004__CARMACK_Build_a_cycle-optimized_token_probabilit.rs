#[repr(align(64))]
pub struct TokenProbCache {
    buckets: [CacheEntry; 256], // power-of-2 for mask-based indexing
    mask: usize,
}

#[derive(Copy, Clone)]
#[repr(align(8))]
struct CacheEntry {
    token_hash: u32,
    prob_fixed: u32,  // 16.16 fixed-point probability
    hit_count: u32,
    _pad: u32,        // cache-line alignment
}

impl TokenProbCache {
    #[inline(always)]
    pub fn new() -> Self {
        Self {
            buckets: [CacheEntry { token_hash: 0, prob_fixed: 0, hit_count: 0, _pad: 0 }; 256],
            mask: 255,
        }
    }

    #[inline(always)]
    pub fn insert(&mut self, token_id: u32, prob: f32) {
        let hash = self.hash(token_id);
        let idx = (hash as usize) & self.mask;
        self.buckets[idx] = CacheEntry {
            token_hash: hash,
            prob_fixed: (prob * 65536.0) as u32,
            hit_count: 0,
            _pad: 0,
        };
    }

    #[inline(always)]
    pub fn lookup(&mut self, token_id: u32) -> Option<f32> {
        let hash = self.hash(token_id);
        let idx = (hash as usize) & self.mask;
        let entry = &mut self.buckets[idx];
        
        // Branchless hit detection: equal -> 0, not_equal -> 1
        let miss = ((entry.token_hash ^ hash) != 0) as u32;
        entry.hit_count += 1 - miss;
        
        // Multiply probability by (1-miss) for branchless return
        let prob_bits = entry.prob_fixed & (0u32.wrapping_sub(1 - miss));
        
        if miss == 0 {
            Some((prob_bits as f32) * (1.0 / 65536.0))
        } else {
            None
        }
    }

    #[inline(always)]
    fn hash(&self, token_id: u32) -> u32 {
        // FNV-1a style inline hash
        let mut h = 2166136261u32;
        h = (h ^ token_id).wrapping_mul(16777619);
        h = (h ^ (token_id >> 16)).wrapping_mul(16777619);
        h
    }

    #[inline(always)]
    pub fn get_stats(&self) -> (u32, u32) {
        let mut hits = 0u32;
        let mut total = 0u32;
        for entry in &self.buckets {
            let valid = (entry.token_hash != 0) as u32;
            hits += entry.hit_count & (0u32.wrapping_sub(valid));
            total += valid;
        }
        (hits, total)
    }
}