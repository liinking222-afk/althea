use std::simd::f32x8;

const DECAY_RATE: f32 = 0.85;
const RECENCY_WEIGHT: f32 = 0.4;
const SEMANTIC_WEIGHT: f32 = 0.6;

#[derive(Clone, Copy)]
#[repr(C, align(32))]
struct MemoryNode {
    timestamp: f32,
    access_count: f32,
    contextual_match: f32,
    strangeness: f32,
    embedding_norm: f32,
    salience: f32,
}

impl MemoryNode {
    #[inline(always)]
    fn compute_salience(&mut self, current_time: f32, query_norm: f32) {
        let time_delta = current_time - self.timestamp;
        let recency_score = (-time_delta * DECAY_RATE).exp();
        let semantic_score = self.contextual_match * query_norm / 
            (self.embedding_norm + 1e-6);
        let access_boost = (self.access_count as f32).ln_1p() * 0.1;
        let strange_multiplier = 1.0 + (self.strangeness * 0.3);
        
        self.salience = (RECENCY_WEIGHT * recency_score + 
                        SEMANTIC_WEIGHT * semantic_score + 
                        access_boost) * strange_multiplier;
    }
}

pub struct SalienceTracker {
    nodes: Vec<MemoryNode>,
    current_time: f32,
}

impl SalienceTracker {
    #[inline(always)]
    pub fn score_batch(&mut self, query_embedding_norm: f32) {
        self.current_time += 1.0;
        
        for node in self.nodes.iter_mut() {
            node.compute_salience(self.current_time, query_embedding_norm);
        }
    }
    
    #[inline(always)]
    pub fn top_k(&mut self, k: usize) -> &[MemoryNode] {
        self.nodes.select_nth_unstable_by(k.min(self.nodes.len()) - 1, 
            |a, b| b.salience.partial_cmp(&a.salience).unwrap());
        &self.nodes[..k.min(self.nodes.len())]
    }
    
    #[inline(always)]
    pub fn register_access(&mut self, index: usize) {
        if let Some(node) = self.nodes.get_mut(index) {
            node.access_count += 1.0;
            node.timestamp = self.current_time;
        }
    }
}